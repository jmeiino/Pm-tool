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


class AIViewSet(viewsets.ViewSet):
    """ViewSet fuer KI-gestuetzte Funktionen."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = AIService()

    @action(detail=False, methods=["post"])
    def prioritize(self, request):
        """Priorisiert eine Liste von Aufgaben."""
        serializer = PrioritizeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = self.service.prioritize_todos(serializer.validated_data["todos"])
            return Response({"result": result, "cached": False})
        except Exception as e:
            logger.error("Fehler bei der Priorisierung: %s", e)
            return Response(
                {"error": "Fehler bei der KI-Verarbeitung."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def summarize(self, request):
        """Fasst Inhalte zusammen."""
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
            return Response(
                {"error": "Fehler bei der KI-Verarbeitung."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="extract-actions")
    def extract_actions(self, request):
        """Extrahiert Aktionspunkte aus Text."""
        serializer = ExtractActionsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = self.service.extract_action_items(serializer.validated_data["text"])
            return Response({"result": result, "cached": False})
        except Exception as e:
            logger.error("Fehler bei der Aktionspunkt-Extraktion: %s", e)
            return Response(
                {"error": "Fehler bei der KI-Verarbeitung."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="daily-plan")
    def daily_plan(self, request):
        """Erstellt einen KI-gestützten Tagesplan."""
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
            return Response(
                {"error": "Fehler bei der KI-Verarbeitung."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def provider(self, request):
        """Gibt den aktuell konfigurierten KI-Provider und die verfuegbaren Provider zurueck."""
        current = getattr(django_settings, "AI_PROVIDER", "claude").lower()

        providers = {
            "claude": {
                "name": "Claude (Anthropic)",
                "model": getattr(django_settings, "ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
                "configured": bool(getattr(django_settings, "ANTHROPIC_API_KEY", "")),
            },
            "ollama": {
                "name": "Ollama (Lokal)",
                "model": getattr(django_settings, "OLLAMA_MODEL", "llama3.1"),
                "configured": True,  # Lokal immer verfuegbar
                "base_url": getattr(django_settings, "OLLAMA_BASE_URL", "http://localhost:11434"),
            },
            "openrouter": {
                "name": "OpenRouter",
                "model": getattr(django_settings, "OPENROUTER_MODEL", "anthropic/claude-sonnet-4"),
                "configured": bool(getattr(django_settings, "OPENROUTER_API_KEY", "")),
            },
        }

        return Response({
            "active_provider": current,
            "active_model": providers.get(current, {}).get("model", ""),
            "providers": providers,
        })
