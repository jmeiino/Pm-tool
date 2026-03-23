from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CalendarEvent, ConfluencePage, GitActivity, IntegrationConfig, SyncLog
from .serializers import (
    CalendarEventSerializer,
    ConfluencePageSerializer,
    GitActivitySerializer,
    IntegrationConfigSerializer,
    SyncLogSerializer,
)


class IntegrationConfigViewSet(viewsets.ModelViewSet):
    """CRUD für Integrations-Konfigurationen des aktuellen Benutzers."""

    serializer_class = IntegrationConfigSerializer

    def get_queryset(self):
        return IntegrationConfig.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """Manuelle Synchronisierung einer Integration auslösen."""
        integration = self.get_object()

        if integration.sync_status == IntegrationConfig.SyncStatus.SYNCING:
            return Response(
                {"detail": "Synchronisierung läuft bereits."},
                status=status.HTTP_409_CONFLICT,
            )

        if not integration.is_enabled:
            return Response(
                {"detail": "Integration ist nicht aktiviert."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        integration.sync_status = IntegrationConfig.SyncStatus.SYNCING
        integration.save(update_fields=["sync_status", "updated_at"])

        # TODO: Celery-Task für die jeweilige Integration auslösen
        # z.B. poll_jira_updates.delay(integration.id)

        return Response(
            {"detail": "Synchronisierung gestartet."},
            status=status.HTTP_202_ACCEPTED,
        )


class SyncLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Nur-Lese-Zugriff auf Sync-Protokolle, gefiltert nach Integration."""

    serializer_class = SyncLogSerializer

    def get_queryset(self):
        qs = SyncLog.objects.filter(integration__user=self.request.user)
        integration_id = self.request.query_params.get("integration")
        if integration_id:
            qs = qs.filter(integration_id=integration_id)
        return qs


class ConfluencePageViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Confluence-Seiten anzeigen und KI-Analyse auslösen."""

    serializer_class = ConfluencePageSerializer
    queryset = ConfluencePage.objects.all()
    filterset_fields = ["space_key"]
    search_fields = ["title", "content_text"]

    @action(detail=True, methods=["post"])
    def analyze(self, request, pk=None):
        """KI-Analyse einer Confluence-Seite auslösen."""
        page = self.get_object()

        # TODO: KI-Analyse als Celery-Task auslösen
        # z.B. analyze_confluence_page.delay(page.id)

        return Response(
            {"detail": "KI-Analyse gestartet.", "page_id": page.id},
            status=status.HTTP_202_ACCEPTED,
        )


class CalendarEventViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Kalender-Termine des aktuellen Benutzers, filterbar nach Zeitraum."""

    serializer_class = CalendarEventSerializer

    def get_queryset(self):
        qs = CalendarEvent.objects.filter(user=self.request.user)
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        if start:
            qs = qs.filter(start_time__gte=start)
        if end:
            qs = qs.filter(end_time__lte=end)
        return qs.order_by("start_time")
