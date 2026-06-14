"""Configuration for the AI layer (phase 4).

Reads settings from environment variables and optionally a .env file in the
project root. No external dependency (no python-dotenv) - we parse .env
ourselves, to keep the toolkit dependency-light.
"""

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"


def _load_dotenv():
    """Load KEY=VALUE lines from .env without overwriting existing env vars."""
    if not _ENV_PATH.exists():
        return
    for raw in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


def _normalize_host(host):
    """Build a client-usable Ollama URL.

    The environment may have OLLAMA_HOST set to the SERVER bind value (e.g.
    '0.0.0.0:11434', without scheme). For a client connection we add a scheme
    and replace 0.0.0.0 with a loopback address.
    """
    host = (host or "").strip().rstrip("/")
    if not host:
        host = "http://127.0.0.1:11434"
    if "://" not in host:
        host = "http://" + host
    return host.replace("//0.0.0.0", "//127.0.0.1")


class Settings:
    # ollama | manual | none
    provider = os.environ.get("LLM_PROVIDER", "ollama").strip().lower()
    ollama_host = _normalize_host(os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    ollama_model = os.environ.get("OLLAMA_MODEL", "qwen3:32b")
    # Generous timeout: a local 32B model can need tens of seconds.
    request_timeout = float(os.environ.get("LLM_TIMEOUT", "180"))


settings = Settings()
