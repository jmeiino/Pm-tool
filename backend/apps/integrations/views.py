from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CalendarEvent, ConfluencePage, GitActivity, GitRepoAnalysis, IntegrationConfig, SyncLog
from .serializers import (
    CalendarEventSerializer,
    ConfluencePageSerializer,
    GitActivitySerializer,
    GitRepoAnalysisSerializer,
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

        # Dispatch to the appropriate Celery task
        if integration.integration_type == IntegrationConfig.IntegrationType.JIRA:
            from apps.integrations.jira.tasks import poll_jira_updates
            poll_jira_updates.delay(integration.id)
        elif integration.integration_type == IntegrationConfig.IntegrationType.CONFLUENCE:
            from apps.integrations.confluence.tasks import poll_confluence_updates
            poll_confluence_updates.delay(integration.id)
        elif integration.integration_type == IntegrationConfig.IntegrationType.GITHUB:
            from apps.integrations.git.tasks import poll_github_updates
            poll_github_updates.delay(integration.id)
        elif integration.integration_type == IntegrationConfig.IntegrationType.MICROSOFT_CALENDAR:
            from apps.integrations.microsoft.tasks import poll_microsoft_calendar
            poll_microsoft_calendar.delay(integration.id)

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

        from apps.integrations.confluence.tasks import analyze_confluence_page_task
        analyze_confluence_page_task.delay(page.id)

        return Response(
            {"detail": "KI-Analyse gestartet.", "page_id": page.id},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"], url_path="create-todos")
    def create_todos(self, request, pk=None):
        """Aufgaben aus Confluence-Aktionspunkten erstellen."""
        page = self.get_object()

        if not page.ai_action_items:
            return Response(
                {"detail": "Keine Aktionspunkte vorhanden. Bitte zuerst analysieren."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.todos.models import PersonalTodo
        created_count = 0
        for action_item in page.ai_action_items:
            title = action_item if isinstance(action_item, str) else action_item.get("action", "")
            if title:
                PersonalTodo.objects.create(
                    user=request.user,
                    title=title,
                    source=PersonalTodo.Source.CONFLUENCE,
                    linked_confluence_page_id=page.confluence_page_id,
                )
                created_count += 1

        return Response(
            {"detail": f"{created_count} Aufgaben erstellt.", "count": created_count},
            status=status.HTTP_201_CREATED,
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


class GitRepoAnalysisViewSet(viewsets.ModelViewSet):
    """GitHub-Repository-Analysen anzeigen, erstellen und KI-Analyse auslösen."""

    serializer_class = GitRepoAnalysisSerializer
    queryset = GitRepoAnalysis.objects.all()
    search_fields = ["repo_full_name", "description"]

    @action(detail=True, methods=["post"])
    def analyze(self, request, pk=None):
        """KI-Analyse eines GitHub-Repositories auslösen."""
        repo = self.get_object()

        from apps.integrations.git.tasks import analyze_github_repo_task
        analyze_github_repo_task.delay(repo.id)

        return Response(
            {"detail": "Repository-Analyse gestartet.", "repo_id": repo.id},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"], url_path="create-todos")
    def create_todos(self, request, pk=None):
        """Aufgaben aus Repository-Verbesserungsvorschlägen erstellen."""
        repo = self.get_object()

        if not repo.ai_action_items:
            return Response(
                {"detail": "Keine Aktionspunkte vorhanden. Bitte zuerst analysieren."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.todos.models import PersonalTodo
        created_count = 0
        for item in repo.ai_action_items:
            title = item if isinstance(item, str) else item.get("action", "")
            if title:
                PersonalTodo.objects.create(
                    user=request.user,
                    title=f"[{repo.repo_full_name}] {title}",
                    source=PersonalTodo.Source.AI,
                    metadata={"source_repo": repo.repo_full_name},
                )
                created_count += 1

        return Response(
            {"detail": f"{created_count} Aufgaben erstellt.", "count": created_count},
            status=status.HTTP_201_CREATED,
        )


class GitActivityViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Git-Aktivitäten anzeigen, filterbar nach Projekt."""

    serializer_class = GitActivitySerializer

    def get_queryset(self):
        qs = GitActivity.objects.all()
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs
