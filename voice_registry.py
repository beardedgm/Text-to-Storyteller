"""
Central registry of all supported Google Cloud TTS en-US voices.

Single source of truth for voice names, display labels, categories,
and gender.  Consumed by config.py (validation), app.py (API endpoint),
and the frontend (dynamic voice selector).
"""

VOICE_CATEGORIES = [
    {"id": "chirp3hd",  "label": "Chirp 3: HD",  "description": "Latest generation, most natural"},
    {"id": "chirphd",   "label": "Chirp HD",      "description": "High-definition neural voices"},
    {"id": "studio",    "label": "Studio",         "description": "Studio-quality narration voices"},
    {"id": "neural2",   "label": "Neural2",        "description": "Second-generation neural voices"},
    {"id": "wavenet",   "label": "WaveNet",        "description": "DeepMind WaveNet synthesis"},
    {"id": "standard",  "label": "Standard",       "description": "Basic synthesis, fastest"},
    {"id": "specialty", "label": "Specialty",       "description": "Purpose-built voices"},
]

VOICES = [
    # ── Chirp 3: HD  (30 voices) ────────────────────────────────
    {"api_name": "en-US-Chirp3-HD-Achernar",     "display_name": "Elena",     "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Achird",        "display_name": "Marcus",    "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Algenib",       "display_name": "Lucas",     "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Algieba",       "display_name": "Nathan",    "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Alnilam",       "display_name": "Oliver",    "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Aoede",         "display_name": "Mia",       "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Autonoe",       "display_name": "Sophia",    "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Callirrhoe",    "display_name": "Isabella",  "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Charon",        "display_name": "Gabriel",   "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Despina",       "display_name": "Natalie",   "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Enceladus",     "display_name": "Benjamin",  "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Erinome",       "display_name": "Charlotte", "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Fenrir",        "display_name": "Erik",      "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Gacrux",        "display_name": "Amelia",    "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Iapetus",       "display_name": "Theodore",  "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Kore",          "display_name": "Lily",      "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Laomedeia",     "display_name": "Victoria",  "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Leda",          "display_name": "Ruby",      "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Orus",          "display_name": "Leo",       "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Puck",          "display_name": "Felix",     "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Pulcherrima",   "display_name": "Aria",      "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Rasalgethi",    "display_name": "Sebastian", "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Sadachbia",     "display_name": "Arthur",    "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Sadaltager",    "display_name": "Owen",      "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Schedar",       "display_name": "Henry",     "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Sulafat",       "display_name": "Maya",      "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Umbriel",       "display_name": "Julian",    "category": "chirp3hd", "gender": "M"},
    {"api_name": "en-US-Chirp3-HD-Vindemiatrix",  "display_name": "Clara",     "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Zephyr",        "display_name": "Willow",    "category": "chirp3hd", "gender": "F"},
    {"api_name": "en-US-Chirp3-HD-Zubenelgenubi", "display_name": "Maxwell",   "category": "chirp3hd", "gender": "M"},

    # ── Chirp HD  (3 voices) ────────────────────────────────────
    {"api_name": "en-US-Chirp-HD-D", "display_name": "Derek",     "category": "chirphd", "gender": "M"},
    {"api_name": "en-US-Chirp-HD-F", "display_name": "Francesca", "category": "chirphd", "gender": "F"},
    {"api_name": "en-US-Chirp-HD-O", "display_name": "Ophelia",   "category": "chirphd", "gender": "F"},

    # ── Studio  (2 voices) ──────────────────────────────────────
    {"api_name": "en-US-Studio-O", "display_name": "Olivia", "category": "studio", "gender": "F"},
    {"api_name": "en-US-Studio-Q", "display_name": "James",  "category": "studio", "gender": "M"},

    # ── Neural2  (9 voices) ─────────────────────────────────────
    {"api_name": "en-US-Neural2-A", "display_name": "Aaron",  "category": "neural2", "gender": "M"},
    {"api_name": "en-US-Neural2-C", "display_name": "Sarah",  "category": "neural2", "gender": "F"},
    {"api_name": "en-US-Neural2-D", "display_name": "David",  "category": "neural2", "gender": "M"},
    {"api_name": "en-US-Neural2-E", "display_name": "Emma",   "category": "neural2", "gender": "F"},
    {"api_name": "en-US-Neural2-F", "display_name": "Fiona",  "category": "neural2", "gender": "F"},
    {"api_name": "en-US-Neural2-G", "display_name": "Grace",  "category": "neural2", "gender": "F"},
    {"api_name": "en-US-Neural2-H", "display_name": "Hannah", "category": "neural2", "gender": "F"},
    {"api_name": "en-US-Neural2-I", "display_name": "Ian",    "category": "neural2", "gender": "M"},
    {"api_name": "en-US-Neural2-J", "display_name": "Jack",   "category": "neural2", "gender": "M"},

    # ── WaveNet  (10 voices) ────────────────────────────────────
    {"api_name": "en-US-Wavenet-A", "display_name": "Alex",    "category": "wavenet", "gender": "M"},
    {"api_name": "en-US-Wavenet-B", "display_name": "Brian",   "category": "wavenet", "gender": "M"},
    {"api_name": "en-US-Wavenet-C", "display_name": "Chloe",   "category": "wavenet", "gender": "F"},
    {"api_name": "en-US-Wavenet-D", "display_name": "Daniel",  "category": "wavenet", "gender": "M"},
    {"api_name": "en-US-Wavenet-E", "display_name": "Emily",   "category": "wavenet", "gender": "F"},
    {"api_name": "en-US-Wavenet-F", "display_name": "Faith",   "category": "wavenet", "gender": "F"},
    {"api_name": "en-US-Wavenet-G", "display_name": "Georgia", "category": "wavenet", "gender": "F"},
    {"api_name": "en-US-Wavenet-H", "display_name": "Holly",   "category": "wavenet", "gender": "F"},
    {"api_name": "en-US-Wavenet-I", "display_name": "Isaac",   "category": "wavenet", "gender": "M"},
    {"api_name": "en-US-Wavenet-J", "display_name": "Jordan",  "category": "wavenet", "gender": "M"},

    # ── Standard  (10 voices) ───────────────────────────────────
    {"api_name": "en-US-Standard-A", "display_name": "Adam",  "category": "standard", "gender": "M"},
    {"api_name": "en-US-Standard-B", "display_name": "Blake", "category": "standard", "gender": "M"},
    {"api_name": "en-US-Standard-C", "display_name": "Cora",  "category": "standard", "gender": "F"},
    {"api_name": "en-US-Standard-D", "display_name": "Dylan", "category": "standard", "gender": "M"},
    {"api_name": "en-US-Standard-E", "display_name": "Eva",   "category": "standard", "gender": "F"},
    {"api_name": "en-US-Standard-F", "display_name": "Freya", "category": "standard", "gender": "F"},
    {"api_name": "en-US-Standard-G", "display_name": "Gwen",  "category": "standard", "gender": "F"},
    {"api_name": "en-US-Standard-H", "display_name": "Hazel", "category": "standard", "gender": "F"},
    {"api_name": "en-US-Standard-I", "display_name": "Ivan",  "category": "standard", "gender": "M"},
    {"api_name": "en-US-Standard-J", "display_name": "Jason", "category": "standard", "gender": "M"},

    # ── Specialty  (5 voices) ───────────────────────────────────
    {"api_name": "en-US-Casual-K",   "display_name": "Kyle",  "category": "specialty", "gender": "M"},
    {"api_name": "en-US-News-K",     "display_name": "Karen", "category": "specialty", "gender": "F"},
    {"api_name": "en-US-News-L",     "display_name": "Linda", "category": "specialty", "gender": "F"},
    {"api_name": "en-US-News-N",     "display_name": "Nolan", "category": "specialty", "gender": "M"},
    {"api_name": "en-US-Polyglot-1", "display_name": "Marco", "category": "specialty", "gender": "M"},
]

# Derived lookup set — used by config.py for validation
ALLOWED_VOICE_NAMES = {v["api_name"] for v in VOICES}

DEFAULT_VOICE = "en-US-Studio-Q"

# ── Tier Configuration ───────────────────────────────────────────
FREE_TIER_VOICES = {'en-US-Standard-A'}          # Adam only
FREE_TIER_DEFAULT_VOICE = 'en-US-Standard-A'


def get_voices_for_tier(tier):
    """Return (voices, categories, default_voice) for the given tier."""
    if tier in ('patron', 'owner'):
        return VOICES, VOICE_CATEGORIES, DEFAULT_VOICE
    # Free tier: only voices in FREE_TIER_VOICES
    free_voices = [v for v in VOICES if v['api_name'] in FREE_TIER_VOICES]
    free_cats = [c for c in VOICE_CATEGORIES
                 if c['id'] in {v['category'] for v in free_voices}]
    return free_voices, free_cats, FREE_TIER_DEFAULT_VOICE


def get_allowed_voice_names_for_tier(tier):
    """Return set of allowed voice api_names for the given tier."""
    return ALLOWED_VOICE_NAMES if tier in ('patron', 'owner') else FREE_TIER_VOICES
