import os
import base64
import time
import logging
import requests

logger = logging.getLogger(__name__)

TTS_ENDPOINT = 'https://texttospeech.googleapis.com/v1/text:synthesize'


class TTSClient:
    def __init__(self, voice_name='en-US-Studio-Q', language_code='en-US',
                 speaking_rate=0.95, pitch=-2.0, sample_rate_hertz=24000):
        self.api_key = os.environ.get('GOOGLE_API_KEY', '')
        if not self.api_key:
            raise RuntimeError('GOOGLE_API_KEY environment variable is not set')

        self.voice_params = {
            'languageCode': language_code,
            'name': voice_name,
        }
        self.audio_config = {
            'audioEncoding': 'LINEAR16',
            'speakingRate': speaking_rate,
            'pitch': pitch,
            'sampleRateHertz': sample_rate_hertz,
        }

    def synthesize_chunk(self, ssml: str) -> bytes:
        """Send a single SSML chunk to Google TTS and return raw WAV bytes."""
        payload = {
            'input': {'ssml': ssml},
            'voice': self.voice_params,
            'audioConfig': self.audio_config,
        }

        resp = requests.post(
            TTS_ENDPOINT,
            params={'key': self.api_key},
            json=payload,
            timeout=30,
        )

        if resp.status_code != 200:
            error_msg = resp.json().get('error', {}).get('message', resp.text)
            raise RuntimeError(f'Google TTS API error ({resp.status_code}): {error_msg}')

        audio_b64 = resp.json().get('audioContent', '')
        if not audio_b64:
            raise RuntimeError('Google TTS returned empty audio content')

        return base64.b64decode(audio_b64)

    def synthesize_all(self, ssml_chunks: list, progress_callback=None) -> list:
        """Synthesize all chunks with rate limiting and progress tracking."""
        wav_segments = []
        total = len(ssml_chunks)

        for i, chunk in enumerate(ssml_chunks):
            try:
                wav_data = self.synthesize_chunk(chunk)
                wav_segments.append(wav_data)
            except Exception as e:
                logger.error(f"TTS synthesis failed on chunk {i+1}/{total}: {e}")
                time.sleep(2)
                try:
                    wav_data = self.synthesize_chunk(chunk)
                    wav_segments.append(wav_data)
                except Exception as retry_err:
                    logger.error(f"Retry also failed: {retry_err}")
                    raise RuntimeError(
                        f"TTS synthesis failed on chunk {i+1}: {retry_err}"
                    )

            if progress_callback:
                progress_callback(i + 1, total)

            # Rate limiting: ~6.7 req/sec, under 500 RPM Studio limit
            if i < total - 1:
                time.sleep(0.15)

        return wav_segments
