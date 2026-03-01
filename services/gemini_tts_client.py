import os
import re
import base64
import struct
import time
import logging
import requests

logger = logging.getLogger(__name__)


def _pcm_to_wav(pcm_bytes, sample_rate=24000, bits_per_sample=16, channels=1):
    """Wrap raw PCM bytes in a standard WAV header.

    Gemini TTS returns raw PCM (Linear16) audio.  The WavConcatenator
    expects valid WAV segments, so we prepend the RIFF/fmt/data headers.
    """
    data_size = len(pcm_bytes)
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8

    header = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')
    header += struct.pack(
        '<4sIHHIIHH',
        b'fmt ', 16, 1, channels,
        sample_rate, byte_rate, block_align, bits_per_sample,
    )
    header += struct.pack('<4sI', b'data', data_size)
    return header + pcm_bytes


def prepare_text_for_gemini(text_chunk: str) -> str:
    """Convert a text chunk with [SECTION_BREAK_N] markers to clean text.

    Gemini TTS accepts plain text (not SSML), so we replace the structural
    markers inserted by MarkdownProcessor with paragraph breaks.
    """
    text = re.sub(r'\[SECTION_BREAK_\d\]', '\n\n', text_chunk)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class GeminiTTSClient:
    """TTS client for Google Gemini models (gemini-2.5-flash-preview-tts).

    Provides the same interface as TTSClient (synthesize_chunk /
    synthesize_all) so the background job runner can use either client
    interchangeably.
    """

    MODEL = 'gemini-2.5-flash-preview-tts'
    ENDPOINT = (
        'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{MODEL}:generateContent'
    )

    def __init__(self, voice_name='Zephyr', chunk_delay=0.5, system_instruction=None):
        self.api_key = os.environ.get('GEMINI_API_KEY', '')
        if not self.api_key:
            raise RuntimeError('GEMINI_API_KEY environment variable is not set')

        self.voice_name = voice_name
        self.chunk_delay = chunk_delay
        self.system_instruction = system_instruction

    def synthesize_chunk(self, text: str) -> bytes:
        """Send a single text chunk to Gemini TTS and return WAV bytes."""
        # Gemini TTS doesn't support systemInstruction — style prompts
        # must be prepended directly to the text content.
        if self.system_instruction:
            text = f'{self.system_instruction}\n\n{text}'

        payload = {
            'contents': [{'parts': [{'text': text}]}],
            'generationConfig': {
                'responseModalities': ['AUDIO'],
                'speechConfig': {
                    'voiceConfig': {
                        'prebuiltVoiceConfig': {
                            'voiceName': self.voice_name,
                        }
                    }
                },
            },
        }

        resp = requests.post(
            self.ENDPOINT,
            params={'key': self.api_key},
            json=payload,
            timeout=60,
        )

        if resp.status_code != 200:
            raw_error = resp.json().get('error', {}).get('message', resp.text)
            logger.error(f'Gemini TTS API error ({resp.status_code}): {raw_error}')
            raise RuntimeError(
                f'Gemini TTS service returned an error (status {resp.status_code})'
            )

        try:
            data = resp.json()
            pcm_b64 = (
                data['candidates'][0]['content']['parts'][0]
                ['inlineData']['data']
            )
        except (KeyError, IndexError, TypeError) as exc:
            logger.error(f'Unexpected Gemini TTS response structure: {exc}')
            raise RuntimeError('Gemini TTS returned an unexpected response format')

        if not pcm_b64:
            raise RuntimeError('Gemini TTS returned empty audio content')

        pcm_bytes = base64.b64decode(pcm_b64)
        return _pcm_to_wav(pcm_bytes)

    def synthesize_all(self, text_chunks: list, progress_callback=None) -> list:
        """Synthesize all chunks with rate limiting and progress tracking.

        Mirrors TTSClient.synthesize_all so the caller doesn't need to
        know which engine is being used.
        """
        wav_segments = []
        total = len(text_chunks)

        for i, chunk in enumerate(text_chunks):
            try:
                wav_data = self.synthesize_chunk(chunk)
                wav_segments.append(wav_data)
            except Exception as e:
                logger.error(f"Gemini TTS failed on chunk {i+1}/{total}: {e}")
                time.sleep(2)
                try:
                    wav_data = self.synthesize_chunk(chunk)
                    wav_segments.append(wav_data)
                except Exception as retry_err:
                    logger.error(
                        f"Retry also failed on chunk {i+1}/{total}: {retry_err}"
                    )
                    raise RuntimeError(
                        f"Audio generation failed on chunk {i+1} of {total}. "
                        f"Please try again."
                    )

            if progress_callback:
                progress_callback(i + 1, total)

            # Rate limiting: Gemini Flash ≈ 150 QPM
            if i < total - 1:
                time.sleep(self.chunk_delay)

        return wav_segments
