# Text to Storyteller — Product Requirements Document

## Overview

Text to Storyteller is a Flask web application that converts written text into narrated audio using Google Cloud Text-to-Speech and Gemini TTS APIs. It supports multi-user authentication, a 7-tier subscription system managed through Patreon OAuth, a library of 99 English voices across 8 categories (powered by two TTS engines), source text management, voice presets, and monthly character usage tracking.

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Flask | 3.1.0 |
| Database | MongoDB (PyMongo) | 4.12.1 |
| TTS API (Cloud) | Google Cloud Text-to-Speech | v1 REST |
| TTS API (Gemini) | Gemini TTS (generativelanguage API) | v1beta REST |
| Production Server | Gunicorn | 23.0.0 |
| Markdown Processing | mistune | 3.1.2 |
| HTTP Client | requests | 2.32.3 |
| Environment | python-dotenv | 1.1.0 |
| Hosting | Render | — |

---

## Project Structure

```
Text-to-Storyteller/
├── app.py                          # Main Flask application
├── config.py                       # Configuration & environment variables
├── models.py                       # MongoDB connection & helpers
├── voice_registry.py               # Voice registry, tier config, helpers
├── requirements.txt                # Python dependencies
├── render.yaml                     # Render deployment config
├── .env.example                    # Environment variable template
├── services/
│   ├── __init__.py
│   ├── markdown_processor.py       # Markdown → narrator-friendly text
│   ├── text_chunker.py             # Text chunking for TTS byte limits
│   ├── tts_client.py               # Google Cloud TTS API client
│   ├── gemini_tts_client.py        # Gemini TTS API client + PCM-to-WAV
│   ├── ssml_builder.py             # SSML generation (Cloud TTS only)
│   └── wav_concatenator.py         # WAV segment concatenation
├── static/
│   ├── css/style.css               # All application styles
│   └── js/app.js                   # Frontend logic
└── templates/
    ├── base.html                   # Base layout (nav, footer, common scripts)
    ├── landing.html                # Public marketing page
    ├── pricing.html                # Subscription tier comparison
    ├── login.html                  # Login form
    ├── register.html               # Registration form
    ├── index.html                  # Main TTS interface
    ├── library.html                # Audio file library & player
    ├── texts.html                  # Source text manager
    └── profile.html                # User profile & settings
```

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google Cloud API key for Cloud TTS voices |
| `GEMINI_API_KEY` | Google AI Studio API key for Gemini TTS voices |

### Application (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | Auto-generated | Flask session secret. Auto-generated if unset (sessions won't survive restarts) |
| `FLASK_DEBUG` | `0` | Debug mode (`0` or `1`) |
| `REGISTRATION_ENABLED` | `1` | Allow new user registration (`0` or `1`) |
| `PORT` | `5000` | Server port |
| `DATA_DIR` | `./instance/` | Root data directory for persistent storage |

### MongoDB

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME` | `storyteller` | Database name |

MongoDB connection pool: min 5, max 50 connections. Server selection timeout: 5 seconds.

### Google Cloud TTS

| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_VOICE_NAME` | `en-US-Wavenet-D` | Default voice |
| `TTS_SPEAKING_RATE` | `0.95` | Default speaking rate (0.25–4.0) |
| `TTS_PITCH` | `-2.0` | Default pitch (-20.0–20.0) |

Fixed settings (not configurable): language `en-US`, sample rate `24000 Hz`, encoding `LINEAR16`, max bytes per request `4800`.

### Patreon OAuth (Optional)

| Variable | Description |
|----------|-------------|
| `PATREON_CLIENT_ID` | OAuth application client ID |
| `PATREON_CLIENT_SECRET` | OAuth application client secret |
| `PATREON_REDIRECT_URI` | Callback URL (e.g., `https://yourapp.com/api/patreon/callback`) |
| `PATREON_CAMPAIGN_ID` | Your Patreon campaign ID |

---

## Database Schema

### `users`

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Primary key |
| `email` | String | Unique, login identifier |
| `password_hash` | String | scrypt hash (werkzeug) |
| `display_name` | String | User-facing name |
| `tier` | String | `free`, `adventurer`, `scribe`, `bard`, `archmage`, `deity`, or `owner` |
| `patreon_id` | String | Patreon user ID (if linked) |
| `created_at` | DateTime | Account creation timestamp |
| `usage` | Object | Monthly usage tracking |
| `usage.{YYYY-MM}.chars_used` | Number | Characters consumed this month |

**Indexes:** Unique on `email`.

### `audio_files`

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Primary key |
| `user_id` | ObjectId | FK → `users` |
| `title` | String | User-facing title |
| `filename` | String | UUID-based WAV filename |
| `voice_name` | String | Google TTS voice API name |
| `speaking_rate` | Number | 0.25–4.0 |
| `pitch` | Number | -20.0–20.0 |
| `duration_seconds` | Number | Audio duration |
| `file_size_bytes` | Number | File size on disk |
| `source_text_id` | ObjectId | FK → `source_texts` (nullable) |
| `created_at` | DateTime | Generation timestamp |

**Indexes:** Compound `(user_id, created_at DESC)`.

### `source_texts`

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Primary key |
| `user_id` | ObjectId | FK → `users` |
| `title` | String | User-facing title (max 200 chars) |
| `content` | String | Full text content |
| `file_type` | String | `paste` or `uploaded` |
| `char_count` | Number | Character count |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

**Indexes:** Compound `(user_id, updated_at DESC)`.

### `voice_presets`

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Primary key |
| `user_id` | ObjectId | FK → `users` |
| `name` | String | Preset name |
| `voice_name` | String | Voice API name |
| `speaking_rate` | Number | 0.25–4.0 |
| `pitch` | Number | -20.0–20.0 |
| `created_at` | DateTime | Creation timestamp |

**Indexes:** Unique compound `(user_id, name)`.

---

## Authentication

- **Method:** Flask session-based with signed cookies
- **Password hashing:** scrypt via werkzeug (`generate_password_hash` / `check_password_hash`)
- **Session lifetime:** 24 hours
- **Cookie flags:** `HTTPOnly`, `SameSite=Lax`, `Secure` (production only)
- **Upload limit:** 2 MB (`MAX_CONTENT_LENGTH`)
- **Email enumeration prevention:** Constant-time dummy hash on failed login
- **Rate limiting:** 5 requests per 60 seconds per IP (in-memory, `threading.Lock`-guarded)

### `@login_required` Decorator

All protected routes use a custom `login_required` decorator that:
1. Checks `session['user_id']` exists
2. Validates the user still exists in MongoDB
3. Sets `g.current_user` and `g.current_user_id` for route handlers
4. Returns 401 JSON for `/api/` paths, redirects to `/login` for page routes

### Security Headers (All Responses)

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; media-src 'self' blob:; img-src 'self' data:; font-src 'self'
```

---

## Routes & API Reference

### Page Routes

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/` | GET | No | Landing page (redirects to `/app` if logged in) |
| `/pricing` | GET | No | Subscription tier comparison |
| `/login` | GET, POST | No | Login form |
| `/register` | GET, POST | No | Registration form |
| `/logout` | POST | Yes | Clear session, redirect to `/` |
| `/app` | GET | Yes | Main TTS synthesis interface |
| `/library` | GET | Yes | Audio file library |
| `/texts` | GET | Yes | Source text manager |
| `/profile` | GET | Yes | User profile & settings |

### Profile API

| Endpoint | Method | Body | Description |
|----------|--------|------|-------------|
| `/api/profile/display-name` | POST | `{display_name}` | Update display name (3–30 chars) |
| `/api/profile/email` | POST | `{email, current_password}` | Change email (validates uniqueness) |
| `/api/profile/password` | POST | `{current_password, new_password, confirm_password}` | Change password (min 8 chars) |

### Patreon API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/patreon/link` | GET | Initiate OAuth flow → redirects to Patreon |
| `/api/patreon/callback` | GET | Handle OAuth callback ← Patreon |
| `/api/patreon/unlink` | POST | Disconnect Patreon account |

### Voices & Usage API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/voices` | GET | Returns voices and categories available for user's tier |
| `/api/usage` | GET | Returns current month's character usage, limits, tier info |

### Synthesis API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/synthesize` | POST | Submit TTS job (multipart/form-data). Returns `{job_id, total_chunks}` |
| `/api/status/<job_id>` | GET | Poll job progress. Returns `{status, total_chunks, completed_chunks, error, audio_id}` |
| `/api/stream/<job_id>` | GET | Stream completed WAV audio |

**Synthesize request fields (multipart/form-data):**

| Field | Required | Description |
|-------|----------|-------------|
| `file` | One of `file` or `text` | Upload `.md`, `.txt`, or `.markdown` file |
| `text` | One of `file` or `text` | Plain text content |
| `voice_name` | No | Voice API name (defaults to tier default) |
| `speaking_rate` | No | 0.25–4.0 (default 0.95) |
| `pitch` | No | -20.0–20.0 (default -2.0) |
| `audio_title` | No | Title for the audio file (default "Untitled") |
| `save_text` | No | `"1"` to save source text |
| `text_title` | No | Title for saved source text |
| `source_text_id` | No | Link to existing source text |

**Limits:**
- Max text length: 500,000 characters
- Max chunks per job: 200
- Max concurrent jobs per IP: 2
- Rate limit: 5 requests per 60 seconds per IP

### Library API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/library` | GET | List user's audio files (sorted by newest) |
| `/api/library/<id>/stream` | GET | Stream WAV for browser playback |
| `/api/library/<id>/download` | GET | Download WAV with attachment header |
| `/api/library/<id>` | PUT | Update audio title (`{title}`) |
| `/api/library/<id>` | DELETE | Delete audio file + WAV from disk |

### Source Texts API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/texts` | GET | List user's texts (sorted by newest) |
| `/api/texts` | POST | Save new text (`{title, content, file_type}`) |
| `/api/texts/<id>` | GET | Get text with full content |
| `/api/texts/<id>` | PUT | Update title (`{title}`) |
| `/api/texts/<id>` | DELETE | Delete text (unlinks from audio) |

### Voice Presets API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/presets` | GET | List user's presets (sorted by name) |
| `/api/presets` | POST | Create preset (`{name, voice_name, speaking_rate, pitch}`) |
| `/api/presets/<id>` | PUT | Update preset name (`{name}`) |
| `/api/presets/<id>` | DELETE | Delete preset |

---

## Voice Registry

### Tier Configuration

7 tiers control which voice categories are available, monthly character limits, and commercial use rights.

| Tier | Label | Monthly Chars | Categories | Commercial | Voices |
|------|-------|--------------|------------|------------|--------|
| `free` | Free | 500 | Standard (Adam only) | No | 1 |
| `adventurer` | The Adventurer | 100K | + WaveNet | No | 20 |
| `scribe` | The Scribe | 500K | + Neural2, Specialty | No | 34 |
| `bard` | The Bard | 750K | + Chirp HD, Chirp 3: HD, Gemini | No | 97 |
| `archmage` | The Archmage | 2M | + Studio | Yes | 99 |
| `deity` | The Deity | 5M | All | Yes | 99 |
| `owner` | Owner | Unlimited | All | Yes | 99 |

The free tier uses an `allowed_voices` override to restrict access to a single voice (`en-US-Standard-A` / Adam) rather than all 10 Standard voices. All other tiers use category-based filtering.

### Voice Categories

| Category ID | Label | Count | Engine | Description |
|-------------|-------|-------|--------|-------------|
| `gemini` | Gemini | 30 | `gemini` | Next-gen Gemini TTS with natural expression |
| `chirp3hd` | Chirp 3: HD | 30 | `cloud_tts` | Latest generation, most natural |
| `chirphd` | Chirp HD | 3 | `cloud_tts` | High-definition neural voices |
| `studio` | Studio | 2 | `cloud_tts` | Studio-quality narration |
| `neural2` | Neural2 | 9 | `cloud_tts` | Second-generation neural |
| `wavenet` | WaveNet | 10 | `cloud_tts` | DeepMind WaveNet synthesis |
| `standard` | Standard | 10 | `cloud_tts` | Basic synthesis, fastest |
| `specialty` | Specialty | 5 | `cloud_tts` | Purpose-built (casual, news, polyglot) |

Each category has an `engine` field that determines which TTS client to use. The `get_voice_engine(voice_name)` function resolves this from the voice name.

### Studio Voice Multiplier

Studio voices (`en-US-Studio-O`, `en-US-Studio-Q`) cost **5x characters**. A 1,000-character text synthesized with a Studio voice consumes 5,000 characters from the monthly limit. This multiplier is defined as `STUDIO_CHAR_MULTIPLIER = 5` in `voice_registry.py`.

### Patreon Tier Mapping

Pledge amounts (in cents) map to tiers in descending order:

| Pledge | Tier |
|--------|------|
| >= $249.00 | `deity` |
| >= $99.00 | `archmage` |
| >= $39.00 | `bard` |
| >= $12.00 | `scribe` |
| >= $5.00 | `adventurer` |
| < $5.00 | `free` |

Campaign owners are assigned the `owner` tier (unlimited).

### Helper Functions (`voice_registry.py`)

| Function | Returns | Description |
|----------|---------|-------------|
| `get_tier_config(tier)` | `dict` | Tier config entry, defaults to `free` |
| `get_voices_for_tier(tier)` | `(voices, categories, default_voice)` | Filtered voices and categories for a tier |
| `get_allowed_voice_names_for_tier(tier)` | `set` | Set of allowed voice API names |
| `calculate_char_cost(count, voice)` | `int` | Effective cost (applies Studio 5x multiplier) |
| `map_patreon_amount_to_tier(cents)` | `str` | Tier name from Patreon pledge amount |
| `is_studio_voice(voice_name)` | `bool` | Whether a voice is Studio category |
| `get_voice_category(voice_name)` | `str` | Category ID for a voice |
| `get_voice_engine(voice_name)` | `str` | TTS engine: `'cloud_tts'` or `'gemini'` |
| `get_chunk_delay(voice_name)` | `float` | Seconds between API calls (rate limiting) |

---

## TTS Pipeline

End-to-end flow from text input to stored audio. The pipeline forks after TextChunker based on the selected voice's engine (`cloud_tts` or `gemini`):

```
User Input (.md/.txt/paste)
    │
    ▼
MarkdownProcessor              # Converts markdown → narrator-friendly plain text
    │                           # Headings → [SECTION_BREAK_N] markers
    ▼
TextChunker                     # Splits into <=4800-byte chunks
    │                           # Priority: section breaks > paragraphs > sentences > words
    ▼
    ├─── Cloud TTS Path ──────────────┐     ├─── Gemini Path ─────────────────┐
    │                                 │     │                                  │
    │  SSMLBuilder                    │     │  prepare_text_for_gemini()       │
    │    Converts to SSML             │     │    Strips [SECTION_BREAK_N]      │
    │    BREAK_1→1500ms, _2→1000ms    │     │    markers, returns clean text   │
    │    Paragraphs→500ms             │     │                                  │
    │         │                       │     │         │                        │
    │         ▼                       │     │         ▼                        │
    │  TTSClient                      │     │  GeminiTTSClient                 │
    │    POST texttospeech.google...  │     │    POST generativelanguage...    │
    │    SSML input → WAV output      │     │    Text input → PCM output      │
    │    GOOGLE_API_KEY               │     │    + PCM-to-WAV header wrapping  │
    │                                 │     │    GEMINI_API_KEY                │
    └────────────────┬────────────────┘     └──────────────┬───────────────────┘
                     │                                     │
                     └──────────────┬──────────────────────┘
                                    ▼
                           WavConcatenator         # Concatenates WAV segments
                                    │              # Single: passthrough
                                    │              # Multiple: extract PCM, rebuild WAV header
                                    ▼
                           Disk Storage            # {AUDIO_DIR}/{user_id}/{job_id}.wav
                                    │              # 24kHz, 16-bit, mono WAV
                                    ▼
                           MongoDB                 # audio_files document with metadata
                                                   # includes 'engine' field
```

### Audio Format

- **Encoding:** LINEAR16 (PCM WAV)
- **Sample Rate:** 24,000 Hz
- **Channels:** Mono
- **Bit Depth:** 16-bit

### TTS Rate Limiting

Per-chunk delays are set per voice category to stay within per-project quotas (targeting 80% of each limit to leave headroom for concurrent users):

| Category | Engine | Quota (RPM) | Effective Delay | Effective RPM |
|----------|--------|-------------|-----------------|---------------|
| Gemini | Gemini | 150 | 0.50s | ~120 |
| Chirp 3: HD | Cloud TTS | 200 | 0.375s | ~160 |
| Studio | Cloud TTS | 500 | 0.15s | ~400 |
| Neural2 | Cloud TTS | 1,000 | 0.075s | ~800 |
| Chirp HD | Cloud TTS | 1,000 | 0.075s | ~800 |
| WaveNet | Cloud TTS | 1,000 | 0.075s | ~800 |
| Standard | Cloud TTS | 1,000 | 0.075s | ~800 |
| Specialty | Cloud TTS | 1,000 | 0.075s | ~800 |

Delays are calculated by `voice_registry.get_chunk_delay(voice_name)` and passed to the TTS client at construction time. On failure, both clients retry once after a 2-second backoff.

### Gemini TTS Details

- **Model:** `gemini-2.5-flash-preview-tts`
- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent`
- **Input:** Plain text (not SSML). Section break markers are stripped by `prepare_text_for_gemini()`.
- **Output:** Raw PCM (Linear16, 24kHz, mono) — wrapped in a WAV header by `_pcm_to_wav()` before concatenation.
- **Auth:** `GEMINI_API_KEY` (Google AI Studio key, separate from `GOOGLE_API_KEY`)
- **Timeout:** 60s per chunk (longer than Cloud TTS's 30s due to generative model latency)
- **Voices:** 30 voices using mythological names (Zephyr, Puck, Charon, Kore, etc.) — same voice set as Chirp 3: HD but accessed through the Gemini API
- **Unique features (not yet exposed in UI):** natural language style prompts, inline emotional markup (`[sigh]`, `[laughing]`, `[whispering]`), multi-speaker synthesis

---

## Background Jobs

### In-Memory Job Queue

Jobs are tracked in a process-scoped `dict` (not persistent across restarts). A background cleanup thread removes jobs older than 1 hour.

### Job Lifecycle

1. **Submit** (`POST /api/synthesize`) — Validate input, check rate limits, check character quota. Create job entry with `status='processing'`. Increment monthly usage. Spawn daemon thread.
2. **Process** (worker thread) — Chunk text → prepare (SSML for Cloud TTS, plain text for Gemini) → call TTS API per chunk (with progress tracking) → concatenate WAVs → write to disk → create `audio_files` document → set `status='complete'`.
3. **Poll** (`GET /api/status/<job_id>`) — Client polls for `{status, completed_chunks, total_chunks, error, audio_id}`.
4. **Stream** (`GET /api/stream/<job_id>`) — Serve completed WAV via `send_file()`.

### Thread Safety

- Rate limit state guarded by `threading.Lock()`
- Jobs dict updated from worker threads, read from main thread (GIL-safe for simple dict operations)
- PyMongo handles its own thread safety

---

## Patreon Integration

### OAuth Flow

1. User clicks "Link Patreon" → `GET /api/patreon/link`
2. App generates `state` token, stores in session
3. Redirects to `https://www.patreon.com/oauth2/authorize` with scopes `identity identity.memberships`
4. User authorizes → Patreon redirects to `/api/patreon/callback` with `code` + `state`
5. App validates state, exchanges code for access token via `POST https://www.patreon.com/api/oauth2/token`
6. Fetches identity + membership data from `GET https://www.patreon.com/api/oauth2/v2/identity`
7. Checks for campaign ownership or active patron membership
8. Maps `currently_entitled_amount_cents` to app tier
9. Updates user record with `tier` and `patreon_id`

### Campaign Owner Detection

If the authenticated Patreon user is the creator of the configured campaign (`PATREON_CAMPAIGN_ID`), they receive the `owner` tier with unlimited characters and all voices.

---

## Security

| Measure | Implementation |
|---------|---------------|
| Password hashing | scrypt (werkzeug) |
| Session cookies | HTTPOnly, SameSite=Lax, Secure in production |
| Security headers | CSP, HSTS, X-Frame-Options DENY, nosniff |
| Path traversal prevention | UUID-based filenames, regex validation |
| Rate limiting | Per-IP, in-memory with threading lock |
| Email enumeration | Constant-time password comparison on all attempts |
| Upload validation | File type whitelist (`.md`, `.txt`, `.markdown`), 2 MB limit, UTF-8 check |
| XSS prevention | Jinja2 template auto-escaping |
| Proxy trust | `ProxyFix(x_for=1, x_proto=1, x_host=1)` |

---

## Deployment

### Render Configuration (`render.yaml`)

```yaml
services:
  - type: web
    name: text-to-storyteller
    runtime: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --workers 2 --threads 4 --timeout 300
```

- **Workers:** 2
- **Threads per worker:** 4
- **Request timeout:** 300 seconds (5 minutes, for long TTS jobs)
- **SECRET_KEY:** Auto-generated by Render
- **Sensitive vars** (`MONGO_URI`, `GOOGLE_API_KEY`, Patreon credentials): Set manually in Render dashboard (`sync: false`)

---

## CLI Commands

### Set User Tier

```bash
flask set-tier <email> <tier>
```

Manually assign a tier to a user. Valid tiers: `free`, `adventurer`, `scribe`, `bard`, `archmage`, `deity`, `owner`.

### Purge All Users

```bash
flask purge-users --confirm
```

Deletes all users, audio files, source texts, and voice presets. Requires `--confirm` flag. For development/testing only.

---

## Local Development

```bash
# Clone the repo
git clone https://github.com/beardedgm/Text-to-Storyteller.git
cd Text-to-Storyteller

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — at minimum set GOOGLE_API_KEY

# Start MongoDB
mongod

# Run the app
flask run --debug
```

The app will be available at `http://localhost:5000`.
