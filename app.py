import os
import random
import secrets
import struct
import uuid
import threading
import time
import logging
import re
from collections import defaultdict
from functools import wraps

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for, g
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
from bson import ObjectId

from config import Config
from models import init_db, get_db, utcnow
import click
import requests as http_requests

from voice_registry import (
    VOICES, VOICE_CATEGORIES, DEFAULT_VOICE,
    get_voices_for_tier, get_allowed_voice_names_for_tier,
)
from services.markdown_processor import MarkdownProcessor
from services.text_chunker import TextChunker
from services.ssml_builder import SSMLBuilder
from services.tts_client import TTSClient
from services.wav_concatenator import WavConcatenator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Trust one level of proxy headers (Render, nginx, etc.)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Regex for validating UUID-based WAV filenames (path traversal prevention)
UUID_WAV_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.wav$'
)

# Initialize MongoDB
mongo_db = init_db(app.config['MONGO_URI'], app.config['MONGO_DB_NAME'])

# Email validation regex
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# Random display names assigned to new accounts
DEFAULT_DISPLAY_NAMES = [
    'Wandering Bard', 'Shadow Scribe', 'Tavern Keeper', 'Mystic Narrator',
    'Dungeon Chronicler', 'Fireside Storyteller', 'Rune Reader', 'Lore Weaver',
    'Saga Spinner', 'Page Turner', 'Quill Master', 'Tome Walker',
]

# Ensure data directories exist
os.makedirs(app.config['DATA_DIR'], exist_ok=True)
os.makedirs(app.config['AUDIO_DIR'], exist_ok=True)


# ── Security Headers ────────────────────────────────────────────

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '0'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "media-src 'self' blob:; "
        "img-src 'self' data:; "
        "font-src 'self'"
    )
    return response


# ── Authentication ──────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        try:
            user = mongo_db.users.find_one({'_id': ObjectId(user_id)})
        except Exception:
            user = None
        if not user:
            session.clear()
            return redirect(url_for('login'))
        g.current_user = user
        g.current_user_id = user['_id']
        return f(*args, **kwargs)
    return decorated_function


def get_user_tier(user):
    """Return the user's tier, defaulting to 'free' for legacy users."""
    return user.get('tier', 'free')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('app_page'))

    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = mongo_db.users.find_one({'email': email})
        if user:
            valid = check_password_hash(user['password_hash'], password)
        else:
            # Constant-time: always hash to prevent timing-based email enumeration
            check_password_hash(generate_password_hash('dummy'), password)
            valid = False

        if valid:
            session['user_id'] = str(user['_id'])
            session.permanent = True
            logger.info(f"Login successful: '{email}' from {get_client_ip()}")
            return redirect(url_for('app_page'))
        else:
            logger.warning(f"Failed login attempt for '{email}' from {get_client_ip()}")
            error = 'Invalid email or password'

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('app_page'))

    if not app.config.get('REGISTRATION_ENABLED', True):
        return render_template('login.html', error='Registration is currently disabled')

    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not email or not EMAIL_RE.match(email):
            error = 'Please enter a valid email address'
        elif len(email) > 254:
            error = 'Email address is too long'
        elif mongo_db.users.find_one({'email': email}):
            error = 'Email already registered'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters'
        elif password != confirm:
            error = 'Passwords do not match'
        else:
            client_ip = get_client_ip()
            if not check_rate_limit(client_ip):
                error = 'Too many attempts. Please wait and try again.'
            else:
                display_name = random.choice(DEFAULT_DISPLAY_NAMES)
                result = mongo_db.users.insert_one({
                    'email': email,
                    'display_name': display_name,
                    'password_hash': generate_password_hash(password),
                    'tier': 'free',
                    'created_at': utcnow(),
                })
                session['user_id'] = str(result.inserted_id)
                session.permanent = True
                logger.info(f"New user registered: '{email}' from {get_client_ip()}")
                return redirect(url_for('app_page'))

    return render_template('register.html', error=error)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('landing'))


# ── CLI Commands ────────────────────────────────────────────────

@app.cli.command('set-tier')
@click.argument('email')
@click.argument('tier', type=click.Choice(['free', 'patron', 'owner']))
def set_tier_cmd(email, tier):
    """Set a user's subscription tier. Usage: flask set-tier <email> <free|patron|owner>"""
    result = mongo_db.users.update_one(
        {'email': email}, {'$set': {'tier': tier}}
    )
    if result.matched_count:
        print(f"User '{email}' tier set to '{tier}'.")
    else:
        print(f"User '{email}' not found.")


@app.cli.command('purge-users')
@click.option('--confirm', is_flag=True, help='Required to actually delete data.')
def purge_users_cmd(confirm):
    """Purge ALL users and their related data. Requires --confirm flag."""
    if not confirm:
        print("⚠️  This will DELETE all users, audio files, source texts, and presets.")
        print("   Run with --confirm to proceed.")
        return

    u = mongo_db.users.delete_many({}).deleted_count
    a = mongo_db.audio_files.delete_many({}).deleted_count
    s = mongo_db.source_texts.delete_many({}).deleted_count
    p = mongo_db.voice_presets.delete_many({}).deleted_count
    print(f"Purged: {u} users, {a} audio files, {s} source texts, {p} presets.")


# ── Patreon OAuth ──────────────────────────────────────────────

@app.route('/api/patreon/link')
@login_required
def patreon_link():
    """Initiate Patreon OAuth flow."""
    client_id = app.config.get('PATREON_CLIENT_ID')
    redirect_uri = app.config.get('PATREON_REDIRECT_URI')
    if not client_id or not redirect_uri:
        logger.error("Patreon OAuth not configured (missing CLIENT_ID or REDIRECT_URI)")
        session['flash_message'] = 'Patreon OAuth is not configured.'
        return redirect(url_for('profile_page'))

    state = secrets.token_urlsafe(32)
    session['patreon_oauth_state'] = state

    params = (
        f"response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=identity%20identity.memberships"
        f"&state={state}"
    )
    return redirect(f"https://www.patreon.com/oauth2/authorize?{params}")


@app.route('/api/patreon/callback')
@login_required
def patreon_callback():
    """Handle Patreon OAuth callback — verify membership and set tier."""
    # Validate state
    state = request.args.get('state', '')
    expected = session.pop('patreon_oauth_state', None)
    if not expected or state != expected:
        logger.warning(f"Patreon OAuth state mismatch for user {g.current_user_id}")
        session['flash_message'] = 'Patreon linking failed (invalid state). Please try again.'
        return redirect(url_for('profile_page'))

    code = request.args.get('code')
    if not code:
        session['flash_message'] = 'Patreon linking cancelled.'
        return redirect(url_for('profile_page'))

    # Exchange code for access token
    try:
        token_resp = http_requests.post(
            'https://www.patreon.com/api/oauth2/token',
            data={
                'code': code,
                'grant_type': 'authorization_code',
                'client_id': app.config['PATREON_CLIENT_ID'],
                'client_secret': app.config['PATREON_CLIENT_SECRET'],
                'redirect_uri': app.config['PATREON_REDIRECT_URI'],
            },
            timeout=15,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get('access_token')
    except Exception as e:
        logger.error(f"Patreon token exchange failed: {e}")
        session['flash_message'] = 'Could not connect to Patreon. Please try again.'
        return redirect(url_for('profile_page'))

    # Fetch identity with memberships
    try:
        identity_resp = http_requests.get(
            'https://www.patreon.com/api/oauth2/v2/identity',
            params={
                'include': 'memberships.campaign,campaign',
                'fields[member]': 'patron_status',
                'fields[user]': 'full_name',
            },
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=15,
        )
        identity_resp.raise_for_status()
        identity = identity_resp.json()
    except Exception as e:
        logger.error(f"Patreon identity fetch failed: {e}")
        session['flash_message'] = 'Could not verify Patreon membership. Please try again.'
        return redirect(url_for('profile_page'))

    # Check for campaign ownership and/or active patron membership
    campaign_id = app.config.get('PATREON_CAMPAIGN_ID', '')
    patreon_user_id = identity.get('data', {}).get('id', '')

    # Check if user is the campaign OWNER (creator)
    is_owner = False
    user_campaign = (
        identity.get('data', {})
        .get('relationships', {})
        .get('campaign', {})
        .get('data', {})
        .get('id', '')
    )
    if user_campaign and user_campaign == campaign_id:
        is_owner = True

    # Check for active patron membership on our campaign
    is_active_patron = False
    for item in identity.get('included', []):
        if item.get('type') != 'member':
            continue
        member_campaign = (
            item.get('relationships', {})
            .get('campaign', {})
            .get('data', {})
            .get('id', '')
        )
        patron_status = item.get('attributes', {}).get('patron_status', '')
        if member_campaign == campaign_id and patron_status == 'active_patron':
            is_active_patron = True
            break

    if is_owner:
        mongo_db.users.update_one(
            {'_id': g.current_user_id},
            {'$set': {'tier': 'owner', 'patreon_id': patreon_user_id}},
        )
        logger.info(f"User {g.current_user['email']} recognised as campaign owner (Patreon ID: {patreon_user_id})")
        session['flash_message'] = 'Welcome back, my liege. All voices are at your command.'
    elif is_active_patron:
        mongo_db.users.update_one(
            {'_id': g.current_user_id},
            {'$set': {'tier': 'patron', 'patreon_id': patreon_user_id}},
        )
        logger.info(f"User {g.current_user['email']} upgraded to patron (Patreon ID: {patreon_user_id})")
        session['flash_message'] = 'Patreon linked! You now have access to all 69 premium voices.'
    else:
        mongo_db.users.update_one(
            {'_id': g.current_user_id},
            {'$set': {'patreon_id': patreon_user_id}},
        )
        logger.info(f"User {g.current_user['email']} linked Patreon but no active pledge (ID: {patreon_user_id})")
        session['flash_message'] = 'Patreon account linked, but no active membership found. Subscribe to unlock all voices.'

    return redirect(url_for('profile_page'))


# ── In-memory job tracking ──────────────────────────────────────

jobs = {}

MAX_TEXT_LENGTH = 500_000
MAX_CHUNKS_PER_JOB = 200
MAX_CONCURRENT_JOBS_PER_IP = 2
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 5

rate_limit_lock = threading.Lock()
ip_request_log = defaultdict(list)
ip_active_jobs = defaultdict(int)


def get_client_ip():
    """Return client IP. ProxyFix middleware ensures request.remote_addr
    is the real client IP when behind a trusted reverse proxy."""
    return request.remote_addr or '127.0.0.1'


def check_rate_limit(ip):
    now = time.time()
    with rate_limit_lock:
        ip_request_log[ip] = [
            t for t in ip_request_log[ip]
            if now - t < RATE_LIMIT_WINDOW
        ]
        if len(ip_request_log[ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return False
        ip_request_log[ip].append(now)
        return True


def check_concurrent_limit(ip):
    with rate_limit_lock:
        return ip_active_jobs[ip] < MAX_CONCURRENT_JOBS_PER_IP


def increment_active_jobs(ip):
    with rate_limit_lock:
        ip_active_jobs[ip] += 1


def decrement_active_jobs(ip):
    with rate_limit_lock:
        ip_active_jobs[ip] = max(0, ip_active_jobs[ip] - 1)


ALLOWED_EXTENSIONS = {'.md', '.txt', '.markdown'}


def validate_upload(file):
    """Validate an uploaded file and return (text, extension)."""
    if not file or file.filename == '':
        raise ValueError("No file selected")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type '{ext}' not allowed. Use .md, .txt, or .markdown")

    content = file.read()
    if len(content) > app.config['MAX_CONTENT_LENGTH']:
        raise ValueError("File too large. Maximum size is 2 MB.")

    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("File must be UTF-8 encoded text")

    return text, ext


def wav_duration_seconds(wav_bytes):
    """Extract duration in seconds from WAV file bytes."""
    try:
        if len(wav_bytes) < 44:
            return 0.0
        byte_rate = struct.unpack_from('<I', wav_bytes, 28)[0]
        if byte_rate == 0:
            return 0.0
        pos = 12
        while pos < len(wav_bytes) - 8:
            chunk_id = wav_bytes[pos:pos + 4]
            chunk_size = struct.unpack_from('<I', wav_bytes, pos + 4)[0]
            if chunk_id == b'data':
                return chunk_size / byte_rate
            pos += 8 + chunk_size
        return 0.0
    except Exception:
        return 0.0


# ── TTS Background Job ─────────────────────────────────────────

def process_tts_job(job_id, ssml_chunks, voice_params):
    """Background worker that runs TTS synthesis and concatenation."""
    client_ip = jobs[job_id].get('client_ip', '')
    user_id = jobs[job_id].get('user_id')
    audio_title = jobs[job_id].get('audio_title', 'Untitled')
    source_text_id = jobs[job_id].get('source_text_id')

    try:
        tts = TTSClient(**voice_params)
        concatenator = WavConcatenator()

        def update_progress(completed, total):
            jobs[job_id]['completed_chunks'] = completed

        wav_segments = tts.synthesize_all(ssml_chunks, update_progress)
        output_wav = concatenator.concatenate(wav_segments)

        # Write to persistent storage
        user_dir = os.path.join(app.config['AUDIO_DIR'], str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        output_path = os.path.join(user_dir, f'{job_id}.wav')
        with open(output_path, 'wb') as f:
            f.write(output_wav)

        # Compute metadata
        duration = wav_duration_seconds(output_wav)
        file_size = len(output_wav)

        # Create database record
        audio_doc = {
            'user_id': ObjectId(user_id),
            'title': audio_title,
            'filename': f'{job_id}.wav',
            'voice_name': voice_params['voice_name'],
            'speaking_rate': voice_params['speaking_rate'],
            'pitch': voice_params['pitch'],
            'duration_seconds': duration,
            'file_size_bytes': file_size,
            'source_text_id': ObjectId(source_text_id) if source_text_id else None,
            'created_at': utcnow(),
        }
        result = mongo_db.audio_files.insert_one(audio_doc)

        jobs[job_id]['status'] = 'complete'
        jobs[job_id]['output_path'] = output_path
        jobs[job_id]['audio_id'] = str(result.inserted_id)
        logger.info(f"Job {job_id} complete: {len(ssml_chunks)} chunks")

    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = 'Audio generation failed. Please try again.'
        logger.exception(f"Job {job_id} failed: {e}")
    finally:
        decrement_active_jobs(client_ip)


# ── Page Routes ─────────────────────────────────────────────────

@app.route('/')
def landing():
    if session.get('user_id'):
        return redirect(url_for('app_page'))
    return render_template('landing.html')


@app.route('/app')
@login_required
def app_page():
    flash_msg = session.pop('flash_message', None)
    return render_template('index.html', flash_message=flash_msg)


@app.route('/library')
@login_required
def library_page():
    return render_template('library.html')


@app.route('/texts')
@login_required
def texts_page():
    return render_template('texts.html')


@app.route('/profile')
@login_required
def profile_page():
    flash_msg = session.pop('flash_message', None)
    return render_template('profile.html', flash_message=flash_msg)


# ── API: Profile ───────────────────────────────────────────────

@app.route('/api/profile/display-name', methods=['POST'])
@login_required
def update_display_name():
    data = request.get_json(silent=True) or {}
    name = data.get('display_name', '').strip()
    if not name or len(name) < 3 or len(name) > 30:
        return jsonify({'error': 'Display name must be 3–30 characters'}), 400

    mongo_db.users.update_one(
        {'_id': g.current_user_id}, {'$set': {'display_name': name}}
    )
    return jsonify({'success': True, 'display_name': name})


@app.route('/api/profile/email', methods=['POST'])
@login_required
def update_email():
    data = request.get_json(silent=True) or {}
    new_email = data.get('email', '').strip().lower()
    current_password = data.get('current_password', '')

    if not new_email or not EMAIL_RE.match(new_email):
        return jsonify({'error': 'Please enter a valid email address'}), 400
    if len(new_email) > 254:
        return jsonify({'error': 'Email address is too long'}), 400
    if not check_password_hash(g.current_user['password_hash'], current_password):
        return jsonify({'error': 'Current password is incorrect'}), 403

    # Check uniqueness (exclude self)
    existing = mongo_db.users.find_one({
        'email': new_email, '_id': {'$ne': g.current_user_id}
    })
    if existing:
        return jsonify({'error': 'Email already in use by another account'}), 409

    mongo_db.users.update_one(
        {'_id': g.current_user_id}, {'$set': {'email': new_email}}
    )
    return jsonify({'success': True})


@app.route('/api/profile/password', methods=['POST'])
@login_required
def update_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not check_password_hash(g.current_user['password_hash'], current_password):
        return jsonify({'error': 'Current password is incorrect'}), 403
    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    if new_password != confirm_password:
        return jsonify({'error': 'New passwords do not match'}), 400

    mongo_db.users.update_one(
        {'_id': g.current_user_id},
        {'$set': {'password_hash': generate_password_hash(new_password)}}
    )
    return jsonify({'success': True})


@app.route('/api/patreon/unlink', methods=['POST'])
@login_required
def patreon_unlink():
    mongo_db.users.update_one(
        {'_id': g.current_user_id},
        {'$unset': {'patreon_id': ''}, '$set': {'tier': 'free'}}
    )
    logger.info(f"User {g.current_user['email']} unlinked Patreon, tier reset to free")
    return jsonify({'success': True, 'message': 'Patreon unlinked. Tier reset to free.'})


# ── API: Voices ─────────────────────────────────────────────────

@app.route('/api/voices')
@login_required
def get_voices():
    tier = get_user_tier(g.current_user)
    voices, categories, default = get_voices_for_tier(tier)
    return jsonify({
        'categories': categories,
        'voices': voices,
        'default': default,
        'tier': tier,
    })


# ── API: Voice Presets ──────────────────────────────────────────

@app.route('/api/presets', methods=['GET'])
@login_required
def list_presets():
    presets = list(mongo_db.voice_presets.find(
        {'user_id': g.current_user_id}
    ).sort('name', 1))
    return jsonify({'presets': [_preset_to_dict(p) for p in presets]})


@app.route('/api/presets', methods=['POST'])
@login_required
def create_preset():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    voice_name = data.get('voice_name', '')
    speaking_rate = data.get('speaking_rate', 0.95)
    pitch = data.get('pitch', -2.0)

    if not name or len(name) > 100:
        return jsonify({'error': 'Preset name is required (max 100 chars)'}), 400
    tier = get_user_tier(g.current_user)
    if voice_name not in get_allowed_voice_names_for_tier(tier):
        return jsonify({'error': 'Invalid voice'}), 400

    existing = mongo_db.voice_presets.find_one({
        'user_id': g.current_user_id, 'name': name
    })
    if existing:
        return jsonify({'error': 'A preset with that name already exists'}), 409

    doc = {
        'user_id': g.current_user_id,
        'name': name,
        'voice_name': voice_name,
        'speaking_rate': float(speaking_rate),
        'pitch': float(pitch),
        'created_at': utcnow(),
    }
    result = mongo_db.voice_presets.insert_one(doc)
    doc['_id'] = result.inserted_id
    return jsonify({'preset': _preset_to_dict(doc)}), 201


@app.route('/api/presets/<preset_id>', methods=['PUT'])
@login_required
def update_preset(preset_id):
    try:
        oid = ObjectId(preset_id)
    except Exception:
        return jsonify({'error': 'Invalid preset ID'}), 400

    preset = mongo_db.voice_presets.find_one({
        '_id': oid, 'user_id': g.current_user_id
    })
    if not preset:
        return jsonify({'error': 'Preset not found'}), 404

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name or len(name) > 100:
        return jsonify({'error': 'Name is required (max 100 chars)'}), 400

    duplicate = mongo_db.voice_presets.find_one({
        'user_id': g.current_user_id,
        'name': name,
        '_id': {'$ne': oid},
    })
    if duplicate:
        return jsonify({'error': 'A preset with that name already exists'}), 409

    mongo_db.voice_presets.update_one({'_id': oid}, {'$set': {'name': name}})
    preset['name'] = name
    return jsonify({'preset': _preset_to_dict(preset)})


@app.route('/api/presets/<preset_id>', methods=['DELETE'])
@login_required
def delete_preset(preset_id):
    try:
        oid = ObjectId(preset_id)
    except Exception:
        return jsonify({'error': 'Invalid preset ID'}), 400

    result = mongo_db.voice_presets.delete_one({
        '_id': oid, 'user_id': g.current_user_id
    })
    if result.deleted_count == 0:
        return jsonify({'error': 'Preset not found'}), 404
    return jsonify({'success': True})


def _preset_to_dict(doc):
    return {
        'id': str(doc['_id']),
        'name': doc['name'],
        'voice_name': doc['voice_name'],
        'speaking_rate': doc['speaking_rate'],
        'pitch': doc['pitch'],
        'created_at': doc.get('created_at', '').isoformat() if doc.get('created_at') else None,
    }


# ── API: Source Texts ───────────────────────────────────────────

@app.route('/api/texts', methods=['GET'])
@login_required
def list_texts():
    texts = list(mongo_db.source_texts.find(
        {'user_id': g.current_user_id}
    ).sort('updated_at', -1))
    return jsonify({'texts': [_text_to_dict(t) for t in texts]})


@app.route('/api/texts/<text_id>', methods=['GET'])
@login_required
def get_text(text_id):
    try:
        oid = ObjectId(text_id)
    except Exception:
        return jsonify({'error': 'Invalid text ID'}), 400

    text = mongo_db.source_texts.find_one({
        '_id': oid, 'user_id': g.current_user_id
    })
    if not text:
        return jsonify({'error': 'Text not found'}), 404
    return jsonify({'text': _text_to_dict(text, include_content=True)})


@app.route('/api/texts', methods=['POST'])
@login_required
def save_text():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    content = data.get('content', '')
    file_type = data.get('file_type', 'paste')

    if not title or len(title) > 200:
        return jsonify({'error': 'Title is required (max 200 chars)'}), 400
    if not content.strip():
        return jsonify({'error': 'Content is empty'}), 400

    now = utcnow()
    doc = {
        'user_id': g.current_user_id,
        'title': title,
        'content': content,
        'file_type': file_type,
        'char_count': len(content),
        'created_at': now,
        'updated_at': now,
    }
    result = mongo_db.source_texts.insert_one(doc)
    doc['_id'] = result.inserted_id
    return jsonify({'text': _text_to_dict(doc)}), 201


@app.route('/api/texts/<text_id>', methods=['PUT'])
@login_required
def update_text(text_id):
    try:
        oid = ObjectId(text_id)
    except Exception:
        return jsonify({'error': 'Invalid text ID'}), 400

    text = mongo_db.source_texts.find_one({
        '_id': oid, 'user_id': g.current_user_id
    })
    if not text:
        return jsonify({'error': 'Text not found'}), 404

    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    if not title or len(title) > 200:
        return jsonify({'error': 'Title is required (max 200 chars)'}), 400

    mongo_db.source_texts.update_one(
        {'_id': oid},
        {'$set': {'title': title, 'updated_at': utcnow()}}
    )
    text['title'] = title
    return jsonify({'text': _text_to_dict(text)})


@app.route('/api/texts/<text_id>', methods=['DELETE'])
@login_required
def delete_text(text_id):
    try:
        oid = ObjectId(text_id)
    except Exception:
        return jsonify({'error': 'Invalid text ID'}), 400

    result = mongo_db.source_texts.delete_one({
        '_id': oid, 'user_id': g.current_user_id
    })
    if result.deleted_count == 0:
        return jsonify({'error': 'Text not found'}), 404

    # Unlink audio files that referenced this text
    mongo_db.audio_files.update_many(
        {'source_text_id': oid},
        {'$set': {'source_text_id': None}}
    )
    return jsonify({'success': True})


def _text_to_dict(doc, include_content=False):
    d = {
        'id': str(doc['_id']),
        'title': doc['title'],
        'file_type': doc.get('file_type'),
        'char_count': doc.get('char_count', 0),
        'created_at': doc.get('created_at', '').isoformat() if doc.get('created_at') else None,
        'updated_at': doc.get('updated_at', '').isoformat() if doc.get('updated_at') else None,
    }
    if include_content:
        d['content'] = doc.get('content', '')
    return d


# ── API: Audio Library ──────────────────────────────────────────

@app.route('/api/library', methods=['GET'])
@login_required
def list_audio():
    audio_files = list(mongo_db.audio_files.find(
        {'user_id': g.current_user_id}
    ).sort('created_at', -1))
    return jsonify({'audio_files': [_audio_to_dict(a) for a in audio_files]})


@app.route('/api/library/<audio_id>/stream')
@login_required
def stream_library_audio(audio_id):
    try:
        oid = ObjectId(audio_id)
    except Exception:
        return jsonify({'error': 'Invalid audio ID'}), 400

    audio = mongo_db.audio_files.find_one({
        '_id': oid, 'user_id': g.current_user_id
    })
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404

    if not UUID_WAV_RE.match(audio.get('filename', '')):
        return jsonify({'error': 'Invalid filename'}), 400

    file_path = os.path.join(
        app.config['AUDIO_DIR'], str(g.current_user_id), audio['filename']
    )
    if not os.path.exists(file_path):
        return jsonify({'error': 'Audio file not found on disk'}), 404

    return send_file(file_path, mimetype='audio/wav')


@app.route('/api/library/<audio_id>/download')
@login_required
def download_library_audio(audio_id):
    try:
        oid = ObjectId(audio_id)
    except Exception:
        return jsonify({'error': 'Invalid audio ID'}), 400

    audio = mongo_db.audio_files.find_one({
        '_id': oid, 'user_id': g.current_user_id
    })
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404

    if not UUID_WAV_RE.match(audio.get('filename', '')):
        return jsonify({'error': 'Invalid filename'}), 400

    file_path = os.path.join(
        app.config['AUDIO_DIR'], str(g.current_user_id), audio['filename']
    )
    if not os.path.exists(file_path):
        return jsonify({'error': 'Audio file not found on disk'}), 404

    safe_title = re.sub(r'[^\w\s-]', '', audio['title']).strip() or 'audio'
    return send_file(
        file_path,
        mimetype='audio/wav',
        as_attachment=True,
        download_name=f'{safe_title}.wav',
    )


@app.route('/api/library/<audio_id>', methods=['PUT'])
@login_required
def update_audio(audio_id):
    try:
        oid = ObjectId(audio_id)
    except Exception:
        return jsonify({'error': 'Invalid audio ID'}), 400

    audio = mongo_db.audio_files.find_one({
        '_id': oid, 'user_id': g.current_user_id
    })
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404

    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    if not title or len(title) > 200:
        return jsonify({'error': 'Title is required (max 200 chars)'}), 400

    mongo_db.audio_files.update_one({'_id': oid}, {'$set': {'title': title}})
    audio['title'] = title
    return jsonify({'audio': _audio_to_dict(audio)})


@app.route('/api/library/<audio_id>', methods=['DELETE'])
@login_required
def delete_audio(audio_id):
    try:
        oid = ObjectId(audio_id)
    except Exception:
        return jsonify({'error': 'Invalid audio ID'}), 400

    audio = mongo_db.audio_files.find_one({
        '_id': oid, 'user_id': g.current_user_id
    })
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404

    file_path = os.path.join(
        app.config['AUDIO_DIR'], str(g.current_user_id), audio['filename']
    )
    try:
        os.remove(file_path)
    except OSError:
        pass

    mongo_db.audio_files.delete_one({'_id': oid})
    return jsonify({'success': True})


def _audio_to_dict(doc):
    return {
        'id': str(doc['_id']),
        'title': doc['title'],
        'voice_name': doc['voice_name'],
        'speaking_rate': doc['speaking_rate'],
        'pitch': doc['pitch'],
        'duration_seconds': doc.get('duration_seconds'),
        'file_size_bytes': doc.get('file_size_bytes', 0),
        'source_text_id': str(doc['source_text_id']) if doc.get('source_text_id') else None,
        'created_at': doc.get('created_at', '').isoformat() if doc.get('created_at') else None,
    }


# ── API: Synthesize ─────────────────────────────────────────────

@app.route('/api/synthesize', methods=['POST'])
@login_required
def synthesize():
    try:
        client_ip = get_client_ip()

        if not check_rate_limit(client_ip):
            return jsonify({'error': 'Too many requests. Please wait a minute and try again.'}), 429

        if not check_concurrent_limit(client_ip):
            return jsonify({'error': 'You already have jobs running. Please wait for them to finish.'}), 429

        file_type = 'paste'
        if 'file' in request.files and request.files['file'].filename:
            raw_text, file_type = validate_upload(request.files['file'])
        elif request.form.get('text'):
            raw_text = request.form['text']
            if len(raw_text) > MAX_TEXT_LENGTH:
                return jsonify({'error': f'Text too long. Maximum is {MAX_TEXT_LENGTH // 1000}K characters.'}), 400
        else:
            return jsonify({'error': 'No text or file provided'}), 400

        if not raw_text.strip():
            return jsonify({'error': 'Input text is empty'}), 400

        tier = get_user_tier(g.current_user)
        allowed_voices = get_allowed_voice_names_for_tier(tier)
        tier_default = get_voices_for_tier(tier)[2]
        voice_name = request.form.get('voice_name', tier_default)
        if voice_name not in allowed_voices:
            voice_name = tier_default

        try:
            speaking_rate = float(request.form.get('speaking_rate', Config.TTS_SPEAKING_RATE))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid speaking_rate value'}), 400
        speaking_rate = max(0.25, min(4.0, speaking_rate))

        try:
            pitch = float(request.form.get('pitch', Config.TTS_PITCH))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid pitch value'}), 400
        pitch = max(-20.0, min(20.0, pitch))

        audio_title = (request.form.get('audio_title') or '').strip() or 'Untitled'

        # Optionally save source text or link to existing
        source_text_id = None
        save_text_flag = request.form.get('save_text') == '1'
        text_title = (request.form.get('text_title') or '').strip()
        source_text_id_str = request.form.get('source_text_id', '')

        if source_text_id_str:
            try:
                st_oid = ObjectId(source_text_id_str)
                st = mongo_db.source_texts.find_one({
                    '_id': st_oid, 'user_id': g.current_user_id
                })
                if st:
                    source_text_id = str(st_oid)
            except Exception:
                pass
        elif save_text_flag and text_title:
            now = utcnow()
            result = mongo_db.source_texts.insert_one({
                'user_id': g.current_user_id,
                'title': text_title,
                'content': raw_text,
                'file_type': file_type,
                'char_count': len(raw_text),
                'created_at': now,
                'updated_at': now,
            })
            source_text_id = str(result.inserted_id)

        processor = MarkdownProcessor()
        clean_text = processor.process(raw_text)

        if not clean_text.strip():
            return jsonify({'error': 'No readable text found after processing'}), 400

        chunker = TextChunker(max_bytes=Config.TTS_MAX_BYTES_PER_REQUEST)
        chunks = chunker.chunk(clean_text)

        if not chunks:
            return jsonify({'error': 'Text produced no usable chunks'}), 400

        if len(chunks) > MAX_CHUNKS_PER_JOB:
            return jsonify({
                'error': f'Text is too long ({len(chunks)} chunks). Maximum is {MAX_CHUNKS_PER_JOB} chunks per job.'
            }), 400

        builder = SSMLBuilder()
        ssml_chunks = [builder.build(chunk) for chunk in chunks]

        increment_active_jobs(client_ip)

        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            'status': 'processing',
            'total_chunks': len(ssml_chunks),
            'completed_chunks': 0,
            'error': None,
            'output_path': None,
            'created_at': time.time(),
            'client_ip': client_ip,
            'user_id': str(g.current_user_id),
            'audio_title': audio_title,
            'source_text_id': source_text_id,
            'audio_id': None,
        }

        voice_params = {
            'voice_name': voice_name,
            'speaking_rate': speaking_rate,
            'pitch': pitch,
        }

        thread = threading.Thread(
            target=process_tts_job,
            args=(job_id, ssml_chunks, voice_params),
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'job_id': job_id,
            'total_chunks': len(ssml_chunks),
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception(f"Synthesis request failed: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


@app.route('/api/status/<job_id>')
@login_required
def status(job_id):
    job = jobs.get(job_id)
    if not job or job.get('user_id') != str(g.current_user_id):
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({
        'status': job['status'],
        'total_chunks': job['total_chunks'],
        'completed_chunks': job['completed_chunks'],
        'error': job['error'],
        'audio_id': job.get('audio_id'),
    })


@app.route('/api/stream/<job_id>')
@login_required
def stream(job_id):
    """Serve WAV audio inline for browser playback via <audio> element."""
    job = jobs.get(job_id)
    if not job or job.get('user_id') != str(g.current_user_id):
        return jsonify({'error': 'Job not found'}), 404

    if job['status'] != 'complete':
        return jsonify({'error': 'Job not complete'}), 400

    if not job['output_path'] or not os.path.exists(job['output_path']):
        return jsonify({'error': 'Output file not found'}), 404

    return send_file(job['output_path'], mimetype='audio/wav')


# ── Error Handlers ─────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('login.html', error='Page not found'), 404


@app.errorhandler(500)
def server_error(e):
    logger.exception("Internal server error")
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('login.html', error='Something went wrong'), 500


# ── Cleanup ─────────────────────────────────────────────────────

def cleanup_old_jobs():
    """Clean up in-memory job entries older than 1 hour."""
    while True:
        time.sleep(600)
        try:
            now = time.time()
            expired_jobs = [
                jid for jid, j in jobs.items()
                if now - j.get('created_at', now) > 3600
            ]
            for jid in expired_jobs:
                jobs.pop(jid, None)
        except Exception:
            pass


cleanup_thread = threading.Thread(target=cleanup_old_jobs, daemon=True)
cleanup_thread.start()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, port=port)
