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
    python scripts/generate_samples.py --replace-placeholders  # replace short placeholder WAVs
    python scripts/generate_samples.py --status      # show which samples are real vs placeholder

Requires GOOGLE_API_KEY (Cloud TTS) and/or GEMINI_API_KEY environment variables.
"""

import argparse
import math
import os
import struct
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

# Real samples are typically 600-800 KB; placeholders are ~47 KB
PLACEHOLDER_SIZE_THRESHOLD = 100_000  # bytes


def sample_path(api_name: str) -> str:
    return os.path.join(SAMPLES_DIR, f'{api_name}.wav')


def is_placeholder(path: str) -> bool:
    """Check if a sample file is a placeholder (short tone) vs real audio."""
    if not os.path.exists(path):
        return False
    return os.path.getsize(path) < PLACEHOLDER_SIZE_THRESHOLD


def create_placeholder_wav(path: str, duration_sec: float = 1.0,
                           sample_rate: int = 24000) -> int:
    """Create a short WAV with a brief tone as a placeholder.

    Returns the total file size in bytes.
    """
    num_samples = int(sample_rate * duration_sec)
    tone_samples = int(sample_rate * 0.3)
    data = bytearray()
    for i in range(num_samples):
        if i < tone_samples:
            val = int(6000 * math.sin(2 * math.pi * 440 * i / sample_rate))
        else:
            val = 0
        data.extend(struct.pack('<h', val))

    data_size = len(data)
    header = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')
    fmt = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 1,
                      sample_rate, sample_rate * 2, 2, 16)
    data_header = struct.pack('<4sI', b'data', data_size)

    with open(path, 'wb') as f:
        f.write(header + fmt + data_header + bytes(data))
    return data_size + 44


def _is_chirp_voice(api_name: str) -> bool:
    """Chirp-HD and Chirp3-HD voices don't support pitch adjustment."""
    return 'Chirp' in api_name


def generate_cloud_tts_sample(voice: dict) -> bytes:
    """Generate a sample using Google Cloud TTS.

    Chirp-HD and Chirp3-HD voices don't support pitch parameters, so
    we use pitch=0 for those.  Chirp-HD voices also reject SSML and
    speed changes, so we fall back to the raw REST API with plain text.
    """
    api_name = voice['api_name']
    delay = get_chunk_delay(api_name)
    is_chirp = _is_chirp_voice(api_name)

    # Chirp-HD (non-3) voices reject SSML and speed/pitch entirely —
    # use the REST API directly with plain text.
    if api_name.startswith('en-US-Chirp-HD-'):
        import base64
        import requests
        resp = requests.post(
            'https://texttospeech.googleapis.com/v1/text:synthesize',
            params={'key': os.environ.get('GOOGLE_API_KEY', '')},
            json={
                'input': {'text': SAMPLE_TEXT},
                'voice': {'languageCode': 'en-US', 'name': api_name},
                'audioConfig': {
                    'audioEncoding': 'LINEAR16',
                    'sampleRateHertz': 24000,
                },
            },
        )
        if not resp.ok:
            err = resp.json().get('error', {}).get('message', resp.text)
            raise RuntimeError(f'TTS error ({resp.status_code}): {err}')
        return base64.b64decode(resp.json()['audioContent'])

    # Chirp3-HD voices support speed but not pitch
    pitch = 0.0 if is_chirp else CLOUD_TTS_PITCH

    client = TTSClient(
        voice_name=api_name,
        speaking_rate=CLOUD_TTS_RATE,
        pitch=pitch,
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


def show_status():
    """Print a summary of real vs placeholder vs missing samples."""
    real, placeholder, missing = [], [], []
    for v in VOICES:
        path = sample_path(v['api_name'])
        if os.path.exists(path):
            if is_placeholder(path):
                placeholder.append(v)
            else:
                real.append(v)
        else:
            missing.append(v)

    print(f'=== Sample Status ===')
    print(f'  Real samples:        {len(real)}')
    print(f'  Placeholder samples: {len(placeholder)}')
    print(f'  Missing:             {len(missing)}')
    print()

    if placeholder:
        cats = {}
        for v in placeholder:
            cats.setdefault(v['category'], []).append(v['display_name'])
        print('Placeholder voices (need regeneration):')
        for cat, names in sorted(cats.items()):
            print(f'  {cat} ({len(names)}): {", ".join(names)}')
        print()

    if missing:
        print('Missing voices (no file at all):')
        for v in missing:
            print(f'  {v["display_name"]} ({v["api_name"]})')


def main():
    parser = argparse.ArgumentParser(
        description='Generate voice preview samples'
    )
    parser.add_argument(
        '--force', action='store_true',
        help='Regenerate all samples (including real ones)',
    )
    parser.add_argument(
        '--replace-placeholders', action='store_true',
        help='Replace placeholder WAVs with real samples',
    )
    parser.add_argument(
        '--voice',
        help='Generate for a specific voice (api_name or display_name)',
    )
    parser.add_argument(
        '--category',
        help='Generate for a specific category only',
    )
    parser.add_argument(
        '--status', action='store_true',
        help='Show sample status and exit',
    )
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    os.makedirs(SAMPLES_DIR, exist_ok=True)

    # Filter voices
    voices = list(VOICES)
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
    failed_voices = []

    print(f'Generating samples for {total} voices...')
    print(f'Output: {os.path.abspath(SAMPLES_DIR)}')
    print()

    for i, voice in enumerate(voices, 1):
        path = sample_path(voice['api_name'])
        label = f"[{i}/{total}] {voice['display_name']} ({voice['api_name']})"

        # Skip logic
        if os.path.exists(path) and not args.force:
            if args.replace_placeholders and is_placeholder(path):
                pass  # Will regenerate below
            else:
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
                # Gemini free tier: 3 RPM → 21s between calls
                # Cloud TTS: much higher limits → 0.3s between calls
                delay = 21.0 if engine == 'gemini' else 0.3
                time.sleep(delay)

        except Exception as e:
            err_str = str(e)
            print(f' FAILED: {err_str[:100]}')
            failed += 1
            failed_voices.append(voice)

            # On rate limit errors, wait longer before continuing
            if '429' in err_str:
                print('    Rate limited — waiting 60s...', flush=True)
                time.sleep(60)

    # Create placeholders for any failures (so the app doesn't break)
    if failed_voices:
        print()
        print(f'Creating placeholder WAVs for {len(failed_voices)} failed voices...')
        for voice in failed_voices:
            path = sample_path(voice['api_name'])
            if not os.path.exists(path):
                create_placeholder_wav(path)
                print(f'  PLACEHOLDER  {voice["display_name"]}')

    print()
    print(f'Done: {generated} generated, {skipped} skipped, {failed} failed')
    if failed_voices:
        print(f'Failed voices: {[v["api_name"] for v in failed_voices]}')
        print()
        print('To regenerate failed voices later:')
        print('  python scripts/generate_samples.py --replace-placeholders')


if __name__ == '__main__':
    main()
