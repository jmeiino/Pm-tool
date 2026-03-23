import abc
import json
import logging
import re

import anthropic
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


class BaseAIClient(abc.ABC):
    """Gemeinsame Schnittstelle fuer alle KI-Provider."""

    default_model: str = ""

    @abc.abstractmethod
    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 4096) -> str:
        """Generiert eine Textantwort."""

    def generate_json(self, prompt: str, system_prompt: str = None, max_tokens: int = 4096) -> dict:
        """Generiert eine JSON-Antwort und parst diese."""
        raw = self.generate(prompt, system_prompt=system_prompt, max_tokens=max_tokens)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
            if match:
                return json.loads(match.group(1).strip())
            raise ValueError(f"Konnte JSON nicht aus der Antwort parsen: {raw[:200]}")


class ClaudeClient(BaseAIClient):
    """Client fuer die Anthropic Claude API."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.default_model = getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 4096) -> str:
        kwargs = {
            "model": self.default_model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        try:
            response = self.client.messages.create(**kwargs)
            return response.content[0].text
        except anthropic.APIError as e:
            logger.error("Claude API Fehler: %s", e)
            raise


class OllamaClient(BaseAIClient):
    """Client fuer eine lokale Ollama-Instanz (OpenAI-kompatible API)."""

    def __init__(self):
        self.base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.default_model = getattr(settings, "OLLAMA_MODEL", "llama3.1")
        self.client = httpx.Client(base_url=self.base_url, timeout=120.0)

    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 4096) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.default_model,
            "messages": messages,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }

        try:
            response = self.client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except httpx.HTTPError as e:
            logger.error("Ollama API Fehler: %s", e)
            raise


class OpenRouterClient(BaseAIClient):
    """Client fuer die OpenRouter API (OpenAI-kompatibel)."""

    OPENROUTER_BASE = "https://openrouter.ai/api/v1"

    def __init__(self):
        api_key = getattr(settings, "OPENROUTER_API_KEY", "")
        self.default_model = getattr(settings, "OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
        self.client = httpx.Client(
            base_url=self.OPENROUTER_BASE,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": getattr(settings, "OPENROUTER_REFERER", "http://localhost:8000"),
            },
            timeout=120.0,
        )

    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 4096) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        try:
            response = self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            logger.error("OpenRouter API Fehler: %s", e)
            raise


# --- Provider-Factory ---

AI_PROVIDERS = {
    "claude": ClaudeClient,
    "ollama": OllamaClient,
    "openrouter": OpenRouterClient,
}


def get_ai_client(user=None) -> BaseAIClient:
    """Erstellt den KI-Client. Liest zuerst aus User.preferences, dann aus Settings."""
    ai_prefs = {}
    if user:
        prefs = getattr(user, "preferences", {}) or {}
        ai_prefs = prefs.get("ai", {})

    provider = ai_prefs.get("provider", getattr(settings, "AI_PROVIDER", "claude")).lower()
    client_cls = AI_PROVIDERS.get(provider)
    if not client_cls:
        raise ValueError(
            f"Unbekannter KI-Provider: '{provider}'. "
            f"Verfuegbar: {', '.join(AI_PROVIDERS.keys())}"
        )

    client = client_cls.__new__(client_cls)

    if provider == "claude":
        import anthropic as _anthropic
        api_key = ai_prefs.get("claude_api_key") or getattr(settings, "ANTHROPIC_API_KEY", "")
        model = ai_prefs.get("claude_model") or getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        client.client = _anthropic.Anthropic(api_key=api_key)
        client.default_model = model
    elif provider == "ollama":
        base_url = ai_prefs.get("ollama_base_url") or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        model = ai_prefs.get("ollama_model") or getattr(settings, "OLLAMA_MODEL", "llama3.1")
        client.base_url = base_url
        client.default_model = model
        client.client = httpx.Client(base_url=base_url, timeout=120.0)
    elif provider == "openrouter":
        api_key = ai_prefs.get("openrouter_api_key") or getattr(settings, "OPENROUTER_API_KEY", "")
        model = ai_prefs.get("openrouter_model") or getattr(settings, "OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
        client.default_model = model
        client.client = httpx.Client(
            base_url=OpenRouterClient.OPENROUTER_BASE,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": getattr(settings, "OPENROUTER_REFERER", "http://localhost:8000"),
            },
            timeout=120.0,
        )

    return client
