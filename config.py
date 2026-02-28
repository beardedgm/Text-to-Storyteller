import os
import tempfile

from voice_registry import ALLOWED_VOICE_NAMES, DEFAULT_VOICE


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-key')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB upload limit

    # Authentication (legacy single-user values used for DB seeding)
    AUTH_USERNAME = os.environ.get('AUTH_USERNAME', 'ddedmon')
    AUTH_PASSWORD_HASH = os.environ.get('AUTH_PASSWORD_HASH', '')
    REGISTRATION_ENABLED = os.environ.get('REGISTRATION_ENABLED', '1') == '1'

    # MongoDB
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME', 'storyteller')

    # Persistent audio file storage
    DATA_DIR = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(__file__), 'instance'))
    AUDIO_DIR = os.path.join(
        os.environ.get('DATA_DIR', os.path.join(os.path.dirname(__file__), 'instance')),
        'audio'
    )

    # Google Cloud TTS settings
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    TTS_VOICE_NAME = os.environ.get('TTS_VOICE_NAME', DEFAULT_VOICE)
    TTS_LANGUAGE_CODE = 'en-US'
    TTS_MAX_BYTES_PER_REQUEST = 4800  # Safety margin below 5000
    TTS_SPEAKING_RATE = float(os.environ.get('TTS_SPEAKING_RATE', '0.95'))
    TTS_PITCH = float(os.environ.get('TTS_PITCH', '-2.0'))
    TTS_SAMPLE_RATE_HERTZ = 24000

    # Allowed voice names — derived from voice_registry
    ALLOWED_VOICES = ALLOWED_VOICE_NAMES

    # Temporary file storage (for in-progress jobs before persistence)
    TEMP_DIR = tempfile.gettempdir()
