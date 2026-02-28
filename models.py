"""MongoDB connection and collection helpers for Text-to-Storyteller."""

import logging
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING

_logger = logging.getLogger(__name__)

# Module-level references (initialized by init_db)
_client = None
_db = None


def init_db(mongo_uri, db_name='storyteller'):
    """Initialize the MongoDB connection and return the database reference."""
    global _client, _db
    _client = MongoClient(
        mongo_uri,
        maxPoolSize=50,
        minPoolSize=5,
        serverSelectionTimeoutMS=5000,
    )
    _db = _client[db_name]
    try:
        _ensure_indexes()
    except Exception as e:
        _logger.warning(f"Could not create indexes on startup (will retry on first query): {e}")
    return _db


def get_db():
    """Get the database reference. Must call init_db first."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


def close_db():
    """Close the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None


def _ensure_indexes():
    """Create indexes for efficient queries."""
    db = get_db()

    # Users: unique username
    db.users.create_index('username', unique=True)

    # Audio files: user lookup, sorted by creation date
    db.audio_files.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])

    # Source texts: user lookup, sorted by updated date
    db.source_texts.create_index([('user_id', ASCENDING), ('updated_at', DESCENDING)])

    # Voice presets: user lookup, unique name per user
    db.voice_presets.create_index(
        [('user_id', ASCENDING), ('name', ASCENDING)],
        unique=True,
    )


def utcnow():
    """Return current UTC time."""
    return datetime.now(timezone.utc)
