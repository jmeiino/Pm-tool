import json
import logging

import anthropic
from django.conf import settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client für die Kommunikation mit der Claude API."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.default_model = getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 4096) -> str:
        """Generiert eine Textantwort von Claude."""
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

    def generate_json(self, prompt: str, system_prompt: str = None, max_tokens: int = 4096) -> dict:
        """Generiert eine JSON-Antwort von Claude und parst diese."""
        raw = self.generate(prompt, system_prompt=system_prompt, max_tokens=max_tokens)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Versuche JSON aus Markdown-Codeblock zu extrahieren
            import re
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
            if match:
                return json.loads(match.group(1).strip())
            raise ValueError(f"Konnte JSON nicht aus der Antwort parsen: {raw[:200]}")
