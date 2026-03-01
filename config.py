import logging
import os
import secrets
import tempfile
from datetime import timedelta

from voice_registry import ALLOWED_VOICE_NAMES, DEFAULT_VOICE

_config_logger = logging.getLogger(__name__)


class Config:
    # Secret key: require from env in production; auto-generate for dev (sessions
    # won't survive restarts, but that's safe default behavior).
    SECRET_KEY = os.environ.get('SECRET_KEY') or ''
    if not SECRET_KEY:
        SECRET_KEY = secrets.token_hex(32)
        _config_logger.warning(
            "SECRET_KEY not set — using random key. Sessions will not persist across restarts."
        )

    # Session cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_DEBUG', '0') != '1'  # True in prod
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
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

    # Patreon OAuth
    PATREON_CLIENT_ID = os.environ.get('PATREON_CLIENT_ID', '')
    PATREON_CLIENT_SECRET = os.environ.get('PATREON_CLIENT_SECRET', '')
    PATREON_REDIRECT_URI = os.environ.get('PATREON_REDIRECT_URI', '')
    PATREON_CAMPAIGN_ID = os.environ.get('PATREON_CAMPAIGN_ID', '')

    # Temporary file storage (for in-progress jobs before persistence)
    TEMP_DIR = tempfile.gettempdir()
