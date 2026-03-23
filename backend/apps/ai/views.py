import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    DailyPlanRequestSerializer,
    ExtractActionsRequestSerializer,
    PrioritizeRequestSerializer,
    SummarizeRequestSerializer,
)
from .services import AIService

logger = logging.getLogger(__name__)


class AIViewSet(viewsets.ViewSet):
    """ViewSet für KI-gestützte Funktionen."""

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
