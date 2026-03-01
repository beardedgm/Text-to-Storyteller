"""
Central registry of all supported TTS voices.

Single source of truth for voice names, display labels, categories,
engine type, and gender.  Consumed by config.py (validation),
app.py (API endpoint), and the frontend (dynamic voice selector).

Supports two TTS engines:
  - cloud_tts  → Google Cloud Text-to-Speech (SSML input, WAV output)
  - gemini     → Gemini TTS via generativelanguage.googleapis.com (text input, PCM output)
"""

VOICE_CATEGORIES = [
    {"id": "gemini",    "label": "Gemini",         "description": "Next-gen Gemini TTS with natural expression", "engine": "gemini"},
    {"id": "chirp3hd",  "label": "Chirp 3: HD",    "description": "Latest generation, most natural",             "engine": "cloud_tts"},
    {"id": "chirphd",   "label": "Chirp HD",        "description": "High-definition neural voices",               "engine": "cloud_tts"},
    {"id": "studio",    "label": "Studio",           "description": "Studio-quality narration voices",             "engine": "cloud_tts"},
    {"id": "neural2",   "label": "Neural2",          "description": "Second-generation neural voices",             "engine": "cloud_tts"},
    {"id": "wavenet",   "label": "WaveNet",          "description": "DeepMind WaveNet synthesis",                  "engine": "cloud_tts"},
    {"id": "standard",  "label": "Standard",         "description": "Basic synthesis, fastest",                    "engine": "cloud_tts"},
    {"id": "specialty", "label": "Specialty",         "description": "Purpose-built voices",                       "engine": "cloud_tts"},
]

VOICES = [
    # ── Gemini  (30 voices) ────────────────────────────────────────
    {"api_name": "Achernar",       "display_name": "Achernar",       "category": "gemini", "gender": "F"},
    {"api_name": "Achird",         "display_name": "Achird",         "category": "gemini", "gender": "M"},
    {"api_name": "Algenib",        "display_name": "Algenib",        "category": "gemini", "gender": "M"},
    {"api_name": "Algieba",        "display_name": "Algieba",        "category": "gemini", "gender": "M"},
    {"api_name": "Alnilam",        "display_name": "Alnilam",        "category": "gemini", "gender": "M"},
    {"api_name": "Aoede",          "display_name": "Aoede",          "category": "gemini", "gender": "F"},
    {"api_name": "Autonoe",        "display_name": "Autonoe",        "category": "gemini", "gender": "F"},
    {"api_name": "Callirrhoe",     "display_name": "Callirrhoe",     "category": "gemini", "gender": "F"},
    {"api_name": "Charon",         "display_name": "Charon",         "category": "gemini", "gender": "M"},
    {"api_name": "Despina",        "display_name": "Despina",        "category": "gemini", "gender": "F"},
    {"api_name": "Enceladus",      "display_name": "Enceladus",      "category": "gemini", "gender": "M"},
    {"api_name": "Erinome",        "display_name": "Erinome",        "category": "gemini", "gender": "F"},
    {"api_name": "Fenrir",         "display_name": "Fenrir",         "category": "gemini", "gender": "M"},
    {"api_name": "Gacrux",         "display_name": "Gacrux",         "category": "gemini", "gender": "F"},
    {"api_name": "Iapetus",        "display_name": "Iapetus",        "category": "gemini", "gender": "M"},
    {"api_name": "Kore",           "display_name": "Kore",           "category": "gemini", "gender": "F"},
    {"api_name": "Laomedeia",      "display_name": "Laomedeia",      "category": "gemini", "gender": "F"},
    {"api_name": "Leda",           "display_name": "Leda",           "category": "gemini", "gender": "F"},
    {"api_name": "Orus",           "display_name": "Orus",           "category": "gemini", "gender": "M"},
    {"api_name": "Puck",           "display_name": "Puck",           "category": "gemini", "gender": "M"},
    {"api_name": "Pulcherrima",    "display_name": "Pulcherrima",    "category": "gemini", "gender": "F"},
    {"api_name": "Rasalgethi",     "display_name": "Rasalgethi",     "category": "gemini", "gender": "M"},
    {"api_name": "Sadachbia",      "display_name": "Sadachbia",      "category": "gemini", "gender": "M"},
    {"api_name": "Sadaltager",     "display_name": "Sadaltager",     "category": "gemini", "gender": "M"},
    {"api_name": "Schedar",        "display_name": "Schedar",        "category": "gemini", "gender": "M"},
    {"api_name": "Sulafat",        "display_name": "Sulafat",        "category": "gemini", "gender": "F"},
    {"api_name": "Umbriel",        "display_name": "Umbriel",        "category": "gemini", "gender": "M"},
    {"api_name": "Vindemiatrix",   "display_name": "Vindemiatrix",   "category": "gemini", "gender": "F"},
    {"api_name": "Zephyr",         "display_name": "Zephyr",         "category": "gemini", "gender": "F"},
    {"api_name": "Zubenelgenubi",  "display_name": "Zubenelgenubi",  "category": "gemini", "gender": "M"},

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

DEFAULT_VOICE = "en-US-Wavenet-D"

# ── Tier Configuration ───────────────────────────────────────────

STUDIO_CHAR_MULTIPLIER = 5  # 1 Studio char costs 5× standard chars

TIER_CONFIG = {
    'free': {
        'label': 'Free',
        'monthly_chars': 500,
        'categories': {'standard'},
        'allowed_voices': {'en-US-Standard-A'},  # Only Adam
        'commercial': False,
        'default_voice': 'en-US-Standard-A',
    },
    'adventurer': {
        'label': 'The Adventurer',
        'monthly_chars': 100_000,
        'categories': {'standard', 'wavenet'},
        'commercial': False,
        'default_voice': 'en-US-Wavenet-D',
    },
    'scribe': {
        'label': 'The Scribe',
        'monthly_chars': 500_000,
        'categories': {'standard', 'wavenet', 'neural2', 'specialty'},
        'commercial': False,
        'default_voice': 'en-US-Wavenet-D',
    },
    'bard': {
        'label': 'The Bard',
        'monthly_chars': 750_000,
        'categories': {'standard', 'wavenet', 'neural2', 'specialty', 'chirphd', 'chirp3hd', 'gemini'},
        'commercial': False,
        'default_voice': 'en-US-Wavenet-D',
    },
    'archmage': {
        'label': 'The Archmage',
        'monthly_chars': 2_000_000,
        'categories': {'standard', 'wavenet', 'neural2', 'specialty', 'chirphd', 'chirp3hd', 'studio', 'gemini'},
        'commercial': True,
        'default_voice': 'en-US-Wavenet-D',
    },
    'deity': {
        'label': 'The Deity',
        'monthly_chars': 5_000_000,
        'categories': {'standard', 'wavenet', 'neural2', 'specialty', 'chirphd', 'chirp3hd', 'studio', 'gemini'},
        'commercial': True,
        'default_voice': 'en-US-Wavenet-D',
    },
    'owner': {
        'label': 'Owner',
        'monthly_chars': None,  # Unlimited
        'categories': {'standard', 'wavenet', 'neural2', 'specialty', 'chirphd', 'chirp3hd', 'studio', 'gemini'},
        'commercial': True,
        'default_voice': 'en-US-Wavenet-D',
    },
}

# All valid tier names
VALID_TIERS = set(TIER_CONFIG.keys())

# ── Narration Moods (Gemini-only systemInstruction presets) ──────

MOODS = [
    {
        'id': 'storyteller',
        'label': 'Storyteller',
        'icon': '\U0001F4D6',
        'description': 'Warm, engaging narrator telling a tale',
        'prompt': (
            'You are a warm, engaging storyteller narrating an adventure. '
            'Speak with a rich, inviting tone that draws listeners into the story. '
            'Vary your pacing naturally \u2014 slow down for suspense, quicken for excitement.'
        ),
    },
    {
        'id': 'dramatic',
        'label': 'Dramatic',
        'icon': '\U0001F3AD',
        'description': 'Theatrical, high-stakes delivery',
        'prompt': (
            'Deliver this with theatrical intensity and dramatic flair. '
            'Emphasize key words, build tension through pauses and vocal dynamics. '
            'Each sentence should feel like the fate of the world hangs on every word.'
        ),
    },
    {
        'id': 'mysterious',
        'label': 'Mysterious',
        'icon': '\U0001F311',
        'description': 'Dark, suspenseful, enigmatic',
        'prompt': (
            'Read this in a dark, mysterious tone full of suspense and intrigue. '
            'Speak softly at times, as if sharing forbidden secrets. '
            'Your voice should evoke shadowy corridors and ancient riddles.'
        ),
    },
    {
        'id': 'calm',
        'label': 'Calm',
        'icon': '\U0001F54A',
        'description': 'Relaxed, measured, soothing',
        'prompt': (
            'Read this in a calm, measured, soothing tone. Speak at a relaxed pace '
            'with gentle emphasis. Your voice should bring peace and clarity '
            'to every word. Avoid urgency or dramatic peaks.'
        ),
    },
    {
        'id': 'epic',
        'label': 'Epic',
        'icon': '\u2694',
        'description': 'Grand, cinematic, heroic',
        'prompt': (
            'Deliver this with grand, epic gravitas befitting a cinematic narrator. '
            'Your voice should swell with heroic energy and authority. '
            'Each sentence should feel like the opening of a legendary saga.'
        ),
    },
    {
        'id': 'whimsical',
        'label': 'Whimsical',
        'icon': '\u2728',
        'description': 'Playful, fairy-tale, lighthearted',
        'prompt': (
            'Read this with a whimsical, playful tone as if telling a fairy tale. '
            'Let your voice dance with lighthearted energy and childlike wonder. '
            'Every sentence should sparkle with enchantment.'
        ),
    },
    {
        'id': 'terrified',
        'label': 'Terrified',
        'icon': '\U0001F631',
        'description': 'Scared, fearful, trembling voice',
        'prompt': (
            'Read this as if you are genuinely terrified. Your voice should tremble '
            'and waver with fear. Speak in hushed, breathless tones, occasionally '
            'quickening as panic sets in. Something horrifying lurks just out of sight.'
        ),
    },
    {
        'id': 'battle_cry',
        'label': 'Battle Cry',
        'icon': '\U0001F4A5',
        'description': 'Intense, commanding, battle energy',
        'prompt': (
            'Deliver this with intense, commanding energy as if rallying troops. '
            'Your voice should be powerful, bold, and electrifying. '
            'Each word should feel like a war cry that could inspire an army to charge.'
        ),
    },
    {
        'id': 'villainous',
        'label': 'Villainous',
        'icon': '\U0001F608',
        'description': 'Menacing, sinister, evil monologue',
        'prompt': (
            'Read this as a menacing villain delivering a sinister monologue. '
            'Speak with dark relish and cruel amusement. Let your voice drip '
            'with malice. Pause for dramatic effect, savoring the fear you inspire.'
        ),
    },
    {
        'id': 'tavern_tale',
        'label': 'Tavern Tale',
        'icon': '\U0001F37A',
        'description': 'Folksy, casual, fireside storytelling',
        'prompt': (
            'Tell this as a friendly tavern keeper sharing a tale over drinks by the fire. '
            'Speak in a folksy, casual, warm manner. Add a conversational quality \u2014 '
            'chuckle at the funny parts, lean in for the juicy bits.'
        ),
    },
    {
        'id': 'sacred',
        'label': 'Sacred',
        'icon': '\U0001F56F',
        'description': 'Reverent, holy, priestly tone',
        'prompt': (
            'Read this with a reverent, sacred tone as if performing a holy ritual. '
            'Speak slowly with measured dignity and solemnity. '
            'Your voice should carry the weight of divine authority.'
        ),
    },
    {
        'id': 'mournful',
        'label': 'Mournful',
        'icon': '\U0001F56F',
        'description': 'Sad, grieving, somber',
        'prompt': (
            'Deliver this with deep sadness and somber grief. Your voice should be '
            'heavy with sorrow, speaking slowly and softly. '
            'Let pauses convey the weight of mourning. Each word should ache.'
        ),
    },
]

_MOOD_BY_ID = {m['id']: m for m in MOODS}
VALID_MOOD_IDS = set(_MOOD_BY_ID.keys())

# Which tiers get which moods. 'custom_mood' = can type a free-text prompt.
MOOD_TIER_CONFIG = {
    'free':       {'allowed_moods': set(),                                                          'custom_mood': False},
    'adventurer': {'allowed_moods': set(),                                                          'custom_mood': False},
    'scribe':     {'allowed_moods': set(),                                                          'custom_mood': False},
    'bard':       {'allowed_moods': {'storyteller', 'calm', 'dramatic', 'mysterious', 'epic'},      'custom_mood': False},
    'archmage':   {'allowed_moods': VALID_MOOD_IDS,                                                 'custom_mood': True},
    'deity':      {'allowed_moods': VALID_MOOD_IDS,                                                 'custom_mood': True},
    'owner':      {'allowed_moods': VALID_MOOD_IDS,                                                 'custom_mood': True},
}


def get_mood_by_id(mood_id):
    """Return the mood dict for a given mood_id, or None."""
    return _MOOD_BY_ID.get(mood_id)


def get_moods_for_tier(tier):
    """Return (moods_list, custom_mood_allowed) for the given tier."""
    cfg = MOOD_TIER_CONFIG.get(tier, MOOD_TIER_CONFIG['free'])
    allowed = cfg['allowed_moods']
    moods = [m for m in MOODS if m['id'] in allowed]
    return moods, cfg['custom_mood']


def validate_mood_for_tier(tier, mood_id=None, custom_prompt=None):
    """Return the validated systemInstruction text, or None.

    Returns None if no mood selected, the tier can't access the mood,
    or custom_prompt is provided but the tier can't use custom moods.
    Custom prompt takes precedence over mood_id if both are provided.
    """
    cfg = MOOD_TIER_CONFIG.get(tier, MOOD_TIER_CONFIG['free'])

    # Custom prompt takes priority
    if custom_prompt and custom_prompt.strip():
        if cfg['custom_mood']:
            return custom_prompt.strip()[:2000]
        return None

    # Preset mood
    if mood_id:
        if mood_id in cfg['allowed_moods']:
            mood = _MOOD_BY_ID.get(mood_id)
            if mood:
                return mood['prompt']
        return None

    return None

# ── TTS rate limits (requests per minute, per project) ───────────

CATEGORY_RATE_LIMITS = {
    'gemini':    150,   # Gemini Flash ~150 QPM
    'chirp3hd':  200,   # Chirp3RequestsPerMinutePerProject
    'studio':    500,   # StudioRequestsPerMinutePerProject
    'neural2':   1000,  # Neural2RequestsPerMinutePerProject
    'chirphd':   1000,  # General RequestsPerMinutePerProject
    'wavenet':   1000,
    'standard':  1000,
    'specialty': 1000,  # PolyglotRequestsPerMinutePerProject (1000)
}


def get_chunk_delay(voice_name):
    """Return the delay in seconds between TTS API calls for this voice.

    Targets 80% of the quota to leave headroom for concurrent users
    sharing the same project quota.
    """
    cat = get_voice_category(voice_name)
    rpm = CATEGORY_RATE_LIMITS.get(cat, 1000)
    safe_rpm = rpm * 0.8
    return 60.0 / safe_rpm


# ── Patreon ↔ App tier mapping (descending by amount) ────────────

PATREON_TIER_MAP = [
    (24900, 'deity'),
    (9900,  'archmage'),
    (3900,  'bard'),
    (1200,  'scribe'),
    (500,   'adventurer'),
]


def map_patreon_amount_to_tier(amount_cents):
    """Map a Patreon pledge amount (in cents) to an app tier."""
    for threshold, tier in PATREON_TIER_MAP:
        if amount_cents >= threshold:
            return tier
    return 'free'


# ── Voice lookup helpers ─────────────────────────────────────────

_VOICE_BY_NAME = {v['api_name']: v for v in VOICES}
_CATEGORY_BY_ID = {c['id']: c for c in VOICE_CATEGORIES}


def get_tier_config(tier):
    """Return the TIER_CONFIG entry for the given tier, defaulting to free."""
    return TIER_CONFIG.get(tier, TIER_CONFIG['free'])


def get_voice_category(voice_name):
    """Return the category id for a voice api_name, or None."""
    v = _VOICE_BY_NAME.get(voice_name)
    return v['category'] if v else None


def get_voice_engine(voice_name):
    """Return the TTS engine for a voice: 'cloud_tts' or 'gemini'."""
    cat = get_voice_category(voice_name)
    cat_info = _CATEGORY_BY_ID.get(cat, {})
    return cat_info.get('engine', 'cloud_tts')


def is_studio_voice(voice_name):
    """Return True if the voice is a Studio-quality voice."""
    return get_voice_category(voice_name) == 'studio'


def calculate_char_cost(char_count, voice_name):
    """Return the effective character cost (Studio voices cost 5×)."""
    if is_studio_voice(voice_name):
        return char_count * STUDIO_CHAR_MULTIPLIER
    return char_count


def get_voices_for_tier(tier):
    """Return (voices, categories, default_voice) for the given tier."""
    cfg = get_tier_config(tier)
    allowed = cfg.get('allowed_voices')
    if allowed:
        tier_voices = [v for v in VOICES if v['api_name'] in allowed]
        tier_cats = [c for c in VOICE_CATEGORIES if c['id'] in {v['category'] for v in tier_voices}]
    else:
        allowed_cats = cfg['categories']
        tier_voices = [v for v in VOICES if v['category'] in allowed_cats]
        tier_cats = [c for c in VOICE_CATEGORIES if c['id'] in allowed_cats]
    return tier_voices, tier_cats, cfg['default_voice']


def get_allowed_voice_names_for_tier(tier):
    """Return set of allowed voice api_names for the given tier."""
    cfg = get_tier_config(tier)
    allowed = cfg.get('allowed_voices')
    if allowed:
        return set(allowed)
    return {v['api_name'] for v in VOICES if v['category'] in cfg['categories']}
