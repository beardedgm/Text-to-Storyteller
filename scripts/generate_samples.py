#!/usr/bin/env python3
"""Generate voice preview samples for all voices.

Run once locally to create static WAV files in static/samples/.
The files are committed to the repo and served directly — zero ongoing
API cost.

Usage:
    python scripts/generate_samples.py              # generate all missing
    python scripts/generate_samples.py --force      # regenerate everything
    python scripts/generate_samples.py --voice Zephyr  # one specific voice
    python scripts/generate_samples.py --category gemini  # one category

Requires GOOGLE_API_KEY and GEMINI_API_KEY environment variables.
"""

import argparse
import os
import sys
import time

# Allow importing from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from voice_registry import VOICES, get_voice_engine, get_chunk_delay
from services.tts_client import TTSClient
from services.ssml_builder import SSMLBuilder
from services.gemini_tts_client import GeminiTTSClient

# ── Configuration ───────────────────────────────────────────────

SAMPLE_TEXT = (
    "The ancient door creaked open, revealing a chamber bathed in "
    "flickering torchlight. Shadows danced along the stone walls as "
    "a faint whisper echoed from deep within."
)

SAMPLES_DIR = os.path.join(
    os.path.dirname(__file__), '..', 'static', 'samples'
)

# Cloud TTS default parameters (match app defaults)
CLOUD_TTS_RATE = 0.95
CLOUD_TTS_PITCH = -2.0


def sample_path(api_name: str) -> str:
    return os.path.join(SAMPLES_DIR, f'{api_name}.wav')


def generate_cloud_tts_sample(voice: dict) -> bytes:
    """Generate a sample using Google Cloud TTS."""
    delay = get_chunk_delay(voice['api_name'])
    client = TTSClient(
        voice_name=voice['api_name'],
        speaking_rate=CLOUD_TTS_RATE,
        pitch=CLOUD_TTS_PITCH,
        chunk_delay=delay,
    )
    builder = SSMLBuilder()
    ssml = builder.build(SAMPLE_TEXT)
    return client.synthesize_chunk(ssml)


def generate_gemini_sample(voice: dict) -> bytes:
    """Generate a sample using Gemini TTS."""
    delay = get_chunk_delay(voice['api_name'])
    client = GeminiTTSClient(
        voice_name=voice['api_name'],
        chunk_delay=delay,
    )
    return client.synthesize_chunk(SAMPLE_TEXT)


def generate_sample(voice: dict) -> bytes:
    """Route to the correct TTS engine for this voice."""
    engine = get_voice_engine(voice['api_name'])
    if engine == 'gemini':
        return generate_gemini_sample(voice)
    return generate_cloud_tts_sample(voice)


def main():
    parser = argparse.ArgumentParser(
        description='Generate voice preview samples'
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Regenerate existing samples',
    )
    parser.add_argument(
        '--voice',
        help='Generate for a specific voice (api_name or display_name)',
    )
    parser.add_argument(
        '--category',
        help='Generate for a specific category only',
    )
    args = parser.parse_args()

    os.makedirs(SAMPLES_DIR, exist_ok=True)

    # Filter voices
    voices = VOICES
    if args.voice:
        v = args.voice
        voices = [
            x for x in voices
            if x['api_name'] == v or x['display_name'].lower() == v.lower()
        ]
        if not voices:
            print(f'Voice not found: {v}')
            sys.exit(1)
    elif args.category:
        voices = [x for x in voices if x['category'] == args.category]
        if not voices:
            print(f'No voices in category: {args.category}')
            sys.exit(1)

    total = len(voices)
    generated = 0
    skipped = 0
    failed = 0

    print(f'Generating samples for {total} voices...')
    print(f'Output: {os.path.abspath(SAMPLES_DIR)}')
    print()

    for i, voice in enumerate(voices, 1):
        path = sample_path(voice['api_name'])
        label = f"[{i}/{total}] {voice['display_name']} ({voice['api_name']})"

        if os.path.exists(path) and not args.force:
            print(f'  SKIP  {label} — already exists')
            skipped += 1
            continue

        try:
            print(f'  GEN   {label}...', end='', flush=True)
            wav_data = generate_sample(voice)

            with open(path, 'wb') as f:
                f.write(wav_data)

            size_kb = len(wav_data) / 1024
            print(f' OK ({size_kb:.0f} KB)')
            generated += 1

            # Rate limiting between voices to avoid quota issues
            if i < total:
                engine = get_voice_engine(voice['api_name'])
                delay = 1.0 if engine == 'gemini' else 0.3
                time.sleep(delay)

        except Exception as e:
            print(f' FAILED: {e}')
            failed += 1

    print()
    print(f'Done: {generated} generated, {skipped} skipped, {failed} failed')


if __name__ == '__main__':
    main()
