import os
import tempfile


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-key')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB upload limit

    # Google Cloud TTS settings
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    TTS_VOICE_NAME = os.environ.get('TTS_VOICE_NAME', 'en-US-Studio-Q')
    TTS_LANGUAGE_CODE = 'en-US'
    TTS_MAX_BYTES_PER_REQUEST = 4800  # Safety margin below 5000
    TTS_SPEAKING_RATE = float(os.environ.get('TTS_SPEAKING_RATE', '0.95'))
    TTS_PITCH = float(os.environ.get('TTS_PITCH', '-2.0'))
    TTS_SAMPLE_RATE_HERTZ = 24000

    # Allowed voice names
    ALLOWED_VOICES = [
        'en-US-Studio-Q',
        'en-US-Studio-O',
        'en-US-Neural2-A',
        'en-US-Neural2-D',
        'en-US-Neural2-J',
    ]

    # Temporary file storage
    TEMP_DIR = tempfile.gettempdir()
