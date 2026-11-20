"""Application configuration, model settings, and API key management."""

import os
from pathlib import Path
from typing import Optional

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
PRIMARY_MODEL_DEFAULT: str = "gemini-3.8-flash"
FALLBACK_MODEL_DEFAULT: str = "gemini-3.5-flash-lite"


def load_api_key(repo_root: Optional[Path] = None) -> Optional[str]:
    """Load the Gemini API key following the strict hierarchy in the spec."""
    root = repo_root or REPO_ROOT

    # 1. Environment variable GEMINI_API_KEY, if set and non-empty.
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    # 2. File named by environment variable GEMINI_API_KEY_FILE.
    env_file = os.environ.get("GEMINI_API_KEY_FILE")
    if env_file:
        file_path = Path(env_file)
        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8").strip()
            if content:
                return content

    # 3. gemini_api_key.txt in the repository root.
    repo_key_file = root / "gemini_api_key.txt"
    if repo_key_file.is_file():
        content = repo_key_file.read_text(encoding="utf-8").strip()
        if content:
            return content

    return None


def get_api_key() -> Optional[str]:
    """Retrieve the active Gemini API key or None if not configured."""
    return load_api_key()


def is_ai_configured() -> bool:
    """Check whether a valid Gemini API key is available."""
    key = get_api_key()
    return bool(key and len(key) > 0)


def get_model() -> str:
    """Retrieve the primary Gemini model name."""
    return os.environ.get("GEMINI_MODEL", PRIMARY_MODEL_DEFAULT)


def get_fallback_model() -> str:
    """Retrieve the fallback Gemini model name."""
    return os.environ.get("GEMINI_FALLBACK_MODEL", FALLBACK_MODEL_DEFAULT)
