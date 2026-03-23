import logging

from django.conf import settings as django_settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .client import AI_PROVIDERS
from .serializers import (
    DailyPlanRequestSerializer,
    ExtractActionsRequestSerializer,
    PrioritizeRequestSerializer,
    SummarizeRequestSerializer,
)
from .services import AIService

logger = logging.getLogger(__name__)


def _get_ai_prefs(user):
    """KI-Einstellungen aus User.preferences lesen (Fallback: Django-Settings)."""
    prefs = getattr(user, "preferences", {}) or {}
    ai = prefs.get("ai", {})
    return {
        "active_provider": ai.get("provider", getattr(django_settings, "AI_PROVIDER", "claude")),
        "claude": {
            "api_key": ai.get("claude_api_key", getattr(django_settings, "ANTHROPIC_API_KEY", "")),
            "model": ai.get("claude_model", getattr(django_settings, "ANTHROPIC_MODEL", "claude-sonnet-4-20250514")),
        },
        "ollama": {
            "base_url": ai.get("ollama_base_url", getattr(django_settings, "OLLAMA_BASE_URL", "http://localhost:11434")),
            "model": ai.get("ollama_model", getattr(django_settings, "OLLAMA_MODEL", "llama3.1")),
        },
        "openrouter": {
            "api_key": ai.get("openrouter_api_key", getattr(django_settings, "OPENROUTER_API_KEY", "")),
            "model": ai.get("openrouter_model", getattr(django_settings, "OPENROUTER_MODEL", "anthropic/claude-sonnet-4")),
        },
    }


class AIViewSet(viewsets.ViewSet):
    """ViewSet fuer KI-gestuetzte Funktionen."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = AIService()

    @action(detail=False, methods=["post"])
    def prioritize(self, request):
        serializer = PrioritizeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = self.service.prioritize_todos(serializer.validated_data["todos"])
            return Response({"result": result, "cached": False})
        except Exception as e:
            logger.error("Fehler bei der Priorisierung: %s", e)
            return Response({"error": "Fehler bei der KI-Verarbeitung."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def summarize(self, request):
        serializer = SummarizeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = self.service.summarize_content(
                serializer.validated_data["content"],
                serializer.validated_data.get("content_type", "text"),
            )
            return Response({"result": result, "cached": False})
        except Exception as e:
            logger.error("Fehler bei der Zusammenfassung: %s", e)
            return Response({"error": "Fehler bei der KI-Verarbeitung."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="extract-actions")
    def extract_actions(self, request):
        serializer = ExtractActionsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = self.service.extract_action_items(serializer.validated_data["text"])
            return Response({"result": result, "cached": False})
        except Exception as e:
            logger.error("Fehler bei der Aktionspunkt-Extraktion: %s", e)
            return Response({"error": "Fehler bei der KI-Verarbeitung."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="daily-plan")
    def daily_plan(self, request):
        serializer = DailyPlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = self.service.suggest_daily_plan(
                serializer.validated_data["todos"],
                serializer.validated_data.get("calendar_events", []),
                serializer.validated_data.get("capacity_hours", 8.0),
            )
            return Response({"result": result, "cached": False})
        except Exception as e:
            logger.error("Fehler bei der Tagesplanung: %s", e)
            return Response({"error": "Fehler bei der KI-Verarbeitung."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get", "patch"])
    def provider(self, request):
        """GET: Aktuelle KI-Einstellungen. PATCH: KI-Einstellungen speichern."""
        if request.method == "PATCH":
            data = request.data
            user = request.user
            prefs = user.preferences or {}
            ai = prefs.get("ai", {})

            # Provider-Auswahl
            if "active_provider" in data:
                provider = data["active_provider"].lower()
                if provider not in AI_PROVIDERS:
                    return Response(
                        {"error": f"Unbekannter Provider: {provider}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                ai["provider"] = provider

            # Claude-Einstellungen
            if "claude" in data:
                claude = data["claude"]
                if "api_key" in claude:
                    ai["claude_api_key"] = claude["api_key"]
                if "model" in claude:
                    ai["claude_model"] = claude["model"]

            # Ollama-Einstellungen
            if "ollama" in data:
                ollama = data["ollama"]
                if "base_url" in ollama:
                    ai["ollama_base_url"] = ollama["base_url"]
                if "model" in ollama:
                    ai["ollama_model"] = ollama["model"]

            # OpenRouter-Einstellungen
            if "openrouter" in data:
                openrouter = data["openrouter"]
                if "api_key" in openrouter:
                    ai["openrouter_api_key"] = openrouter["api_key"]
                if "model" in openrouter:
                    ai["openrouter_model"] = openrouter["model"]

            prefs["ai"] = ai
            user.preferences = prefs
            user.save(update_fields=["preferences"])

        # GET-Antwort (auch nach PATCH)
        ai_prefs = _get_ai_prefs(request.user)
        active = ai_prefs["active_provider"]

        return Response({
            "active_provider": active,
            "active_model": ai_prefs.get(active, {}).get("model", ""),
            "providers": {
                "claude": {
                    "name": "Claude (Anthropic)",
                    "model": ai_prefs["claude"]["model"],
                    "api_key_set": bool(ai_prefs["claude"]["api_key"]),
                },
                "ollama": {
                    "name": "Ollama (Lokal)",
                    "model": ai_prefs["ollama"]["model"],
                    "base_url": ai_prefs["ollama"]["base_url"],
                    "api_key_set": True,
                },
                "openrouter": {
                    "name": "OpenRouter",
                    "model": ai_prefs["openrouter"]["model"],
                    "api_key_set": bool(ai_prefs["openrouter"]["api_key"]),
                },
            },
        })
