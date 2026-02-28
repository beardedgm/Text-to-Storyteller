import os
import uuid
import threading
import time
import logging
from collections import defaultdict
from functools import wraps

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for
from werkzeug.security import check_password_hash

from config import Config
from services.markdown_processor import MarkdownProcessor
from services.text_chunker import TextChunker
from services.ssml_builder import SSMLBuilder
from services.tts_client import TTSClient
from services.wav_concatenator import WavConcatenator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# In-memory job tracking
jobs = {}

# --- Rate limiting & abuse prevention ---
MAX_TEXT_LENGTH = 500_000          # 500 KB of pasted text (~100k words)
MAX_CHUNKS_PER_JOB = 200          # Cap TTS API calls per job
MAX_CONCURRENT_JOBS_PER_IP = 2    # Simultaneous jobs per IP
RATE_LIMIT_WINDOW = 60            # seconds
RATE_LIMIT_MAX_REQUESTS = 5       # max synthesize requests per window per IP

rate_limit_lock = threading.Lock()
ip_request_log = defaultdict(list)   # ip -> [timestamp, ...]
ip_active_jobs = defaultdict(int)    # ip -> count of running jobs


def get_client_ip():
    """Get the real client IP, respecting X-Forwarded-For behind a proxy."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'


def check_rate_limit(ip):
    """Return True if the request is allowed, False if rate-limited."""
    now = time.time()
    with rate_limit_lock:
        # Prune old entries
        ip_request_log[ip] = [
            t for t in ip_request_log[ip]
            if now - t < RATE_LIMIT_WINDOW
        ]
        if len(ip_request_log[ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return False
        ip_request_log[ip].append(now)
        return True


def check_concurrent_limit(ip):
    """Return True if the IP hasn't exceeded concurrent job limit."""
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
    """Validate an uploaded file and return its text content."""
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

    return text


def process_tts_job(job_id, ssml_chunks, voice_params):
    """Background worker that runs TTS synthesis and concatenation."""
    client_ip = jobs[job_id].get('client_ip', '')
    try:
        tts = TTSClient(**voice_params)
        concatenator = WavConcatenator()

        def update_progress(completed, total):
            jobs[job_id]['completed_chunks'] = completed

        wav_segments = tts.synthesize_all(ssml_chunks, update_progress)
        output_wav = concatenator.concatenate(wav_segments)

        output_path = os.path.join(Config.TEMP_DIR, f'{job_id}.wav')
        with open(output_path, 'wb') as f:
            f.write(output_wav)

        jobs[job_id]['status'] = 'complete'
        jobs[job_id]['output_path'] = output_path
        logger.info(f"Job {job_id} complete: {len(ssml_chunks)} chunks")

    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = 'Audio generation failed. Please try again.'
        logger.exception(f"Job {job_id} failed: {e}")
    finally:
        decrement_active_jobs(client_ip)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if (username == app.config['AUTH_USERNAME'] and
                app.config['AUTH_PASSWORD_HASH'] and
                check_password_hash(app.config['AUTH_PASSWORD_HASH'], password)):
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'

    return render_template('login.html', error=error)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/api/synthesize', methods=['POST'])
@login_required
def synthesize():
    try:
        client_ip = get_client_ip()

        # Rate limit check
        if not check_rate_limit(client_ip):
            return jsonify({'error': 'Too many requests. Please wait a minute and try again.'}), 429

        # Concurrent job limit
        if not check_concurrent_limit(client_ip):
            return jsonify({'error': 'You already have jobs running. Please wait for them to finish.'}), 429

        # Get text from file upload or textarea
        if 'file' in request.files and request.files['file'].filename:
            raw_text = validate_upload(request.files['file'])
        elif request.form.get('text'):
            raw_text = request.form['text']
            if len(raw_text) > MAX_TEXT_LENGTH:
                return jsonify({'error': f'Text too long. Maximum is {MAX_TEXT_LENGTH // 1000}K characters.'}), 400
        else:
            return jsonify({'error': 'No text or file provided'}), 400

        if not raw_text.strip():
            return jsonify({'error': 'Input text is empty'}), 400

        # Get voice parameters
        voice_name = request.form.get('voice_name', Config.TTS_VOICE_NAME)
        if voice_name not in Config.ALLOWED_VOICES:
            voice_name = Config.TTS_VOICE_NAME

        speaking_rate = float(request.form.get('speaking_rate', Config.TTS_SPEAKING_RATE))
        speaking_rate = max(0.25, min(4.0, speaking_rate))

        pitch = float(request.form.get('pitch', Config.TTS_PITCH))
        pitch = max(-20.0, min(20.0, pitch))

        # Process markdown
        processor = MarkdownProcessor()
        clean_text = processor.process(raw_text)

        if not clean_text.strip():
            return jsonify({'error': 'No readable text found after processing'}), 400

        # Chunk text
        chunker = TextChunker(max_bytes=Config.TTS_MAX_BYTES_PER_REQUEST)
        chunks = chunker.chunk(clean_text)

        if not chunks:
            return jsonify({'error': 'Text produced no usable chunks'}), 400

        # Cap chunks to prevent API bill abuse
        if len(chunks) > MAX_CHUNKS_PER_JOB:
            return jsonify({
                'error': f'Text is too long ({len(chunks)} chunks). Maximum is {MAX_CHUNKS_PER_JOB} chunks per job.'
            }), 400

        # Build SSML for each chunk
        builder = SSMLBuilder()
        ssml_chunks = [builder.build(chunk) for chunk in chunks]

        # Track concurrent jobs for this IP
        increment_active_jobs(client_ip)

        # Create job
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            'status': 'processing',
            'total_chunks': len(ssml_chunks),
            'completed_chunks': 0,
            'error': None,
            'output_path': None,
            'created_at': time.time(),
            'client_ip': client_ip,
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
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({
        'status': job['status'],
        'total_chunks': job['total_chunks'],
        'completed_chunks': job['completed_chunks'],
        'error': job['error'],
    })


@app.route('/api/download/<job_id>')
@login_required
def download(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if job['status'] != 'complete':
        return jsonify({'error': 'Job not complete'}), 400

    if not job['output_path'] or not os.path.exists(job['output_path']):
        return jsonify({'error': 'Output file not found'}), 404

    return send_file(
        job['output_path'],
        mimetype='audio/wav',
        as_attachment=True,
        download_name='storyteller-output.wav',
    )


# Cleanup old temp files (runs periodically via a background thread)
def cleanup_old_files():
    """Delete WAV files older than 1 hour."""
    while True:
        time.sleep(600)  # Check every 10 minutes
        try:
            now = time.time()
            expired_jobs = [
                jid for jid, j in jobs.items()
                if now - j.get('created_at', now) > 3600
            ]
            for jid in expired_jobs:
                job = jobs.pop(jid, None)
                if job and job.get('output_path'):
                    try:
                        os.remove(job['output_path'])
                    except OSError:
                        pass
        except Exception:
            pass


cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, port=port)
