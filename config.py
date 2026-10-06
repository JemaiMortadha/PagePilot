"""
config.py — Central configuration for FB Page Automation
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project root
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# ── API Keys ────────────────────────────────────────────────
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY", "")
APIFY_API_TOKEN     = os.getenv("APIFY_API_TOKEN", "")
FB_PAGE_ID          = os.getenv("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")

# ── Competitor pages ─────────────────────────────────────────
_raw = os.getenv("COMPETITOR_PAGES", "")
COMPETITOR_PAGES = [p.strip() for p in _raw.split(",") if p.strip()]

# ── Your page brand ──────────────────────────────────────────
PAGE_NAME = os.getenv("PAGE_NAME", "MyPage")

# ── Behaviour ────────────────────────────────────────────────
POSTS_TO_CHECK = int(os.getenv("POSTS_TO_CHECK", "5"))
DEDUP_HOURS    = int(os.getenv("DEDUP_HOURS", "72"))

# ── Paths ────────────────────────────────────────────────────
OUTPUT_DIR   = BASE_DIR / "output"
CACHE_FILE   = BASE_DIR / "seen_posts.json"
STYLE_IMAGE  = BASE_DIR / "style.jpeg"
FONTS_DIR    = BASE_DIR / "fonts"

OUTPUT_DIR.mkdir(exist_ok=True)
FONTS_DIR.mkdir(exist_ok=True)

# ── Image dimensions (matching style.jpeg portrait format) ───
IMAGE_WIDTH  = 1080
IMAGE_HEIGHT = 1350   # 4:5 ratio — ideal for FB/IG feed

# ── Pollinations.ai (truly free, no key needed) ──────────────
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&model=flux&nologo=true&enhance=true"
