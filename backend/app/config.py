"""Read settings from environment variables.

A beginner-friendly note: a `.env` file contains lines like
`AGRIGUIDE_MODE=development`. This module loads those lines into Python so we
can change settings without editing code. Secret keys belong here, never in the
frontend.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# parents[0] = app/, parents[1] = backend/, parents[2] = agri-guide/
BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"

load_dotenv(BACKEND_DIR / ".env")

MODE = os.getenv("AGRIGUIDE_MODE", "development")
RELEASE_VERSION = os.getenv("AGRIGUIDE_VERSION", "1.1.0-live")
API_PREFIX = "/api"

# Cookie auth settings. Secure cookies require HTTPS, so they are only enabled
# in production mode. SameSite=Strict blocks cross-site cookie sending.
COOKIE_SECURE = MODE.strip().lower() == "production"
ADMIN_COOKIE_NAME = "agriguide_admin"
CSRF_COOKIE_NAME = "agriguide_csrf"
# A harmless readable hint so the browser can avoid a 401 probe when signed out.
ADMIN_HINT_COOKIE_NAME = "agriguide_admin_hint"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agri_guide.db")

# Community photos and videos are stored on this server only, never in git or
# in a CDN. Tests point UPLOAD_DIR at a temporary folder.
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "uploads"))).resolve()
UPLOAD_URL_PREFIX = "/uploads"
UPLOAD_MAX_IMAGE_BYTES = 8 * 1024 * 1024
UPLOAD_MAX_VIDEO_BYTES = 60 * 1024 * 1024
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000,http://localhost:8010,http://127.0.0.1:8010,http://localhost:3000,http://127.0.0.1:3000",
)

# Integration settings. Weather and mandi data are fetched live; no fallback
# or sample values are generated when an upstream service is unavailable.
WEATHER_PROVIDER = os.getenv("WEATHER_PROVIDER", "open-meteo")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# Government mandi prices come from data.gov.in's Agmarknet dataset. A shared
# public key is used as a default so the app works out of the box; set your own
# key in backend/.env for deployment. No price is invented or stored locally.
DATA_GOV_API_KEY = os.getenv(
    "DATA_GOV_API_KEY", "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
)

# Natural-language assistant. The key is server-side only; the browser never
# receives it. Set AI_PROVIDER to "openai" (default) or "gemini".
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").strip().lower()
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL") or ("gemini-2.0-flash" if AI_PROVIDER == "gemini" else "gpt-4o-mini")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "20"))
SUPPORTED_VOICE_LANGUAGES = {
    "en": "English",
    "te": "Telugu",
    "hi": "Hindi",
    "ta": "Tamil",
    "mr": "Marathi",
}
