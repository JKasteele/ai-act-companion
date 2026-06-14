"""Ollama provider: calls a local model via the Ollama HTTP API.

Privacy-friendly and free: all data stays on the machine. Requires `httpx` and
a running Ollama instance (see OLLAMA_HOST/OLLAMA_MODEL).
"""

from .base import LLMProvider
from .config import settings


class OllamaProvider(LLMProvider):
    name = "ollama"
    interactive = False

    def __init__(self):
        self.host = settings.ollama_host
        self.model = settings.ollama_model
        self.timeout = settings.request_timeout

    def status(self):
        info = {"provider": self.name, "interactive": False, "available": False,
                "host": self.host, "model": self.model}
        try:
            import httpx
            r = httpx.get(f"{self.host}/api/tags", timeout=4)
            r.raise_for_status()
            models = [m.get("name") for m in r.json().get("models", [])]
            info["available"] = True
            info["models"] = models
            info["model_loaded"] = self.model in models
        except Exception as e:  # noqa: BLE001
            info["error"] = str(e)
        return info

    def generate(self, system, user, as_json=True):
        import httpx
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            # qwen3 is a reasoning model; thinking disabled for speed/parsing.
            "think": False,
            "options": {"temperature": 0.2},
        }
        if as_json:
            payload["format"] = "json"  # forces valid JSON output
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(f"{self.host}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
        return (data.get("message") or {}).get("content", "")
