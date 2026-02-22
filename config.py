"""
Configuration module for GeminiFileStoreManager.
Contains app settings, themes, defaults, and constants.
"""

import os
from pathlib import Path
from typing import Dict, List, Any

# App Info
APP_NAME = "GeminiFileStoreManager"
APP_VERSION = "1.0.0"
APP_MIN_WIDTH = 900
APP_MIN_HEIGHT = 700

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
STORES_FILE = BASE_DIR / "stores.json"
ENV_FILE = BASE_DIR / ".env"
LOG_FILE = BASE_DIR / "app.log"

# Create data directory if not exists
DATA_DIR.mkdir(exist_ok=True)

# Theme Settings
THEME = "darkly"
THEMES = ["darkly", "cyborg", "superhero", "solar", "vapor"]

# Colors for dark theme
COLORS = {
    # Palette inspired by example.html (gold/bronze legal tone)
    "primary": "#c4a47c",
    "secondary": "#444444",
    "success": "#00bc8c",
    "info": "#3498db",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "light": "#e0e0e0",
    "dark": "#0d0d0d",
    "bg": "#0d0d0d",
    "fg": "#e0e0e0",
    "accent": "#c4a47c",
    "grid": "rgba(196,164,124,0.1)",
}

# Preferred fonts (may fallback if not installed)
FONTS = {
    "heading": ("Space Grotesk", 12, "bold"),
    "mono": ("Space Mono", 10),
}

# Chunking Configuration Defaults
CHUNK_DEFAULTS = {
    "max_tokens": 1024,
    "min_tokens": 256,
    "overlap_tokens": 100,
}

CHUNK_LIMITS = {
    "max_tokens": {"min": 200, "max": 2048, "step": 64},
    "overlap_tokens": {"min": 0, "max": 512, "step": 32},
}

# Supported File Types
SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".pdf", ".doc", ".docx",
    ".csv", ".json", ".xml", ".html", ".htm",
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".h",
    ".rb", ".go", ".rs", ".php", ".swift",
}

# Metadata Schema Defaults
METADATA_SCHEMA = {
    "practice": {"type": "text", "label": "Practice", "default": ""},
    "doc_type": {
        "type": "dropdown",
        "label": "Document Type",
        "options": ["Atto", "Contratto", "Sentenza", "Fattura", "Nota", "Altro"],
        "default": "Altro"
    },
    "tags": {"type": "chips", "label": "Tags", "default": []},
    "date": {"type": "date", "label": "Date", "default": ""},
    "client": {"type": "text", "label": "Client", "default": ""},
}

# Gemini API Settings
# Modern 2026 Models from essentials.md
MODELS_2026 = [
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite"
]
GEMINI_MODEL = "gemini-2.0-flash"  # Standard stable modern model
GEMINI_EMBEDDING_MODEL = "models/embedding-001"
API_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# UI Settings
RECENT_STORES_LIMIT = 10
MAX_CHAT_HISTORY = 50
PROGRESS_UPDATE_INTERVAL = 100  # ms
LOG_MAX_LINES = 1000

# File Size Limits (in bytes)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_TOTAL_SIZE = 1024 * 1024 * 1024  # 1GB

# Keyboard Shortcuts
SHORTCUTS = {
    "new_store": "<Control-n>",
    "refresh": "<F5>",
    "query": "<Control-q>",
    "settings": "<Control-comma>",
    "quit": "<Control-q>",
}

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s: %(message)s"
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOG_FILE),
            "formatter": "standard",
            "level": "DEBUG",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": "DEBUG",
    },
}


def get_env_api_key() -> str:
    """Get API key from environment or .env file."""
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
    return os.getenv("GEMINI_API_KEY", "")


def save_api_key(api_key: str) -> None:
    """Save API key to .env file."""
    env_content = f"GEMINI_API_KEY={api_key}\n"
    ENV_FILE.write_text(env_content)


def load_stores_data() -> Dict[str, Any]:
    """Load stores metadata from local JSON file."""
    import json
    if STORES_FILE.exists():
        try:
            with open(STORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"stores": [], "last_updated": ""}
    return {"stores": [], "last_updated": ""}


def save_stores_data(data: Dict[str, Any]) -> None:
    """Save stores metadata to local JSON file."""
    import json
    from datetime import datetime
    data["last_updated"] = datetime.now().isoformat()
    with open(STORES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
