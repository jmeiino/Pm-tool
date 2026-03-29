from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdminUser

from .serializers import AdminUserCreateSerializer, AdminUserSerializer

User = get_user_model()


# ─── Dashboard ────────────────────────────────────────────────────────────────


class AdminDashboardView(APIView):
    """Liefert aggregierte Statistiken fuer das Admin-Dashboard."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.agents.models import AgentTask
        from apps.ai.models import AIResult
        from apps.integrations.models import IntegrationConfig, SyncLog
        from apps.projects.models import Issue, Project
        from apps.todos.models import PersonalTodo

        now = timezone.now()

        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()

        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status="active").count()

        total_issues = Issue.objects.count()
        open_issues = Issue.objects.exclude(status__in=["done", "closed"]).count()

        total_todos = PersonalTodo.objects.count()
        pending_todos = PersonalTodo.objects.filter(status="pending").count()

        sync_errors_24h = SyncLog.objects.filter(
            status="failed",
            started_at__gte=now - timedelta(hours=24),
        ).count()

        integrations_active = IntegrationConfig.objects.filter(is_enabled=True).count()
        integrations_error = IntegrationConfig.objects.filter(sync_status="error").count()

        ai_tokens_30d = (
            AIResult.objects.filter(created_at__gte=now - timedelta(days=30))
            .aggregate(total=Sum("tokens_used"))
            .get("total")
            or 0
        )
        ai_results_30d = AIResult.objects.filter(
            created_at__gte=now - timedelta(days=30)
        ).count()

        agent_tasks_active = AgentTask.objects.filter(
            status__in=["pending", "assigned", "in_progress", "review", "needs_input"]
        ).count()
        agent_tasks_total = AgentTask.objects.count()

        return Response(
            {
                "users": {
                    "total": total_users,
                    "active": active_users,
                },
                "projects": {
                    "total": total_projects,
                    "active": active_projects,
                },
                "issues": {
                    "total": total_issues,
                    "open": open_issues,
                },
                "todos": {
                    "total": total_todos,
                    "pending": pending_todos,
                },
                "integrations": {
                    "active": integrations_active,
                    "error": integrations_error,
                },
                "sync": {
                    "errors_24h": sync_errors_24h,
                },
                "ai": {
                    "tokens_30d": ai_tokens_30d,
                    "results_30d": ai_results_30d,
                },
                "agents": {
                    "active_tasks": agent_tasks_active,
                    "total_tasks": agent_tasks_total,
                },
            }
        )


# ─── Benutzerverwaltung ──────────────────────────────────────────────────────


class AdminUserListCreateView(generics.ListCreateAPIView):
    """Liste aller Benutzer + Erstellen neuer Benutzer."""

    permission_classes = [IsAdminUser]
    queryset = User.objects.all().order_by("-date_joined")
    filterset_fields = ["is_active", "is_staff"]
    search_fields = ["username", "email", "first_name", "last_name"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminUserCreateSerializer
        return AdminUserSerializer


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Einzelnen Benutzer anzeigen, bearbeiten oder deaktivieren."""

    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all()

    def perform_destroy(self, instance):
        """Soft-Delete: Benutzer deaktivieren statt loeschen."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])


# ─── System Health ────────────────────────────────────────────────────────────


class SystemHealthView(APIView):
    """Prueft den Status von Datenbank, Redis und Celery."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        health = {}

        # Datenbank
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health["database"] = {"status": "ok"}
        except Exception as e:
            health["database"] = {"status": "error", "detail": str(e)}

        # Redis
        try:
            from django.core.cache import cache

            cache.set("health_check", "ok", 10)
            val = cache.get("health_check")
            health["redis"] = {"status": "ok" if val == "ok" else "error"}
        except Exception as e:
            health["redis"] = {"status": "error", "detail": str(e)}

        # Celery
        try:
            from config.celery import app as celery_app

            inspector = celery_app.control.inspect(timeout=2.0)
            active = inspector.active()
            if active is not None:
                worker_count = len(active)
                health["celery"] = {"status": "ok", "workers": worker_count}
            else:
                health["celery"] = {"status": "error", "detail": "Keine Worker erreichbar"}
        except Exception as e:
            health["celery"] = {"status": "error", "detail": str(e)}

        return Response(health)


# ─── Integrationen ────────────────────────────────────────────────────────────


class AdminIntegrationsView(generics.ListAPIView):
    """Alle Integrations-Konfigurationen aller Benutzer."""

    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        from apps.integrations.models import IntegrationConfig

        configs = IntegrationConfig.objects.select_related("user").all().order_by("-updated_at")

        integration_type = request.query_params.get("type")
        if integration_type:
            configs = configs.filter(integration_type=integration_type)

        sync_status = request.query_params.get("status")
        if sync_status:
            configs = configs.filter(sync_status=sync_status)

        data = []
        for config in configs:
            data.append(
                {
                    "id": config.id,
                    "user_id": config.user_id,
                    "username": config.user.username,
                    "user_full_name": config.user.get_full_name() or config.user.username,
                    "integration_type": config.integration_type,
                    "is_enabled": config.is_enabled,
                    "sync_status": config.sync_status,
                    "last_synced_at": config.last_synced_at,
                    "created_at": config.created_at,
                    "updated_at": config.updated_at,
                }
            )

        return Response(data)


class AdminForceSyncView(APIView):
    """Synchronisierung einer Integration erzwingen."""

    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        from apps.integrations.models import IntegrationConfig
        from apps.integrations.views import IntegrationConfigViewSet

        try:
            integration = IntegrationConfig.objects.get(pk=pk)
        except IntegrationConfig.DoesNotExist:
            return Response(
                {"detail": "Integration nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not integration.is_enabled:
            return Response(
                {"detail": "Integration ist nicht aktiviert."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        IntegrationConfigViewSet._dispatch_sync(integration)

        return Response(
            {"detail": "Synchronisierung gestartet."},
            status=status.HTTP_202_ACCEPTED,
        )


class AdminSyncLogsView(generics.ListAPIView):
    """Alle Sync-Logs mit Filtern."""

    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        from apps.integrations.models import SyncLog

        qs = SyncLog.objects.select_related("integration", "integration__user").order_by(
            "-started_at"
        )

        log_status = request.query_params.get("status")
        if log_status:
            qs = qs.filter(status=log_status)

        integration_id = request.query_params.get("integration")
        if integration_id:
            qs = qs.filter(integration_id=integration_id)

        # Letzte 200 Eintraege
        qs = qs[:200]

        data = []
        for log in qs:
            data.append(
                {
                    "id": log.id,
                    "integration_id": log.integration_id,
                    "integration_type": log.integration.integration_type,
                    "username": log.integration.user.username,
                    "direction": log.direction,
                    "status": log.status,
                    "records_processed": log.records_processed,
                    "records_created": log.records_created,
                    "records_updated": log.records_updated,
                    "errors": log.errors,
                    "started_at": log.started_at,
                    "completed_at": log.completed_at,
                }
            )

        return Response(data)


# ─── AI Stats ─────────────────────────────────────────────────────────────────


class AdminAIStatsView(APIView):
    """AI-Nutzungsstatistiken."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.ai.models import AIResult

        now = timezone.now()

        # Gesamtstatistiken
        total = AIResult.objects.count()
        total_tokens = AIResult.objects.aggregate(t=Sum("tokens_used")).get("t") or 0

        # Letzte 30 Tage
        recent = AIResult.objects.filter(created_at__gte=now - timedelta(days=30))
        recent_count = recent.count()
        recent_tokens = recent.aggregate(t=Sum("tokens_used")).get("t") or 0

        # Nach Model
        by_model = list(
            recent.values("model_used")
            .annotate(count=Count("id"), tokens=Sum("tokens_used"))
            .order_by("-count")
        )

        # Nach Typ
        by_type = list(
            recent.values("result_type")
            .annotate(count=Count("id"), tokens=Sum("tokens_used"))
            .order_by("-count")
        )

        # Cache-Stats (Eintraege die noch gueltig sind)
        cached_valid = AIResult.objects.filter(expires_at__gt=now).count()

        return Response(
            {
                "total_results": total,
                "total_tokens": total_tokens,
                "recent_30d": {
                    "count": recent_count,
                    "tokens": recent_tokens,
                },
                "by_model": by_model,
                "by_type": by_type,
                "cache": {
                    "valid_entries": cached_valid,
                },
            }
        )


# ─── Agent Overview ───────────────────────────────────────────────────────────


class AdminAgentOverviewView(APIView):
    """Uebersicht ueber Agent-Companies und Tasks."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.agents.models import AgentCompanyConfig, AgentProfile, AgentTask

        companies = []
        for company in AgentCompanyConfig.objects.select_related("user").all():
            companies.append(
                {
                    "id": company.id,
                    "name": company.name,
                    "user": company.user.username,
                    "base_url": company.base_url,
                    "is_enabled": company.is_enabled,
                }
            )

        task_stats = {
            "total": AgentTask.objects.count(),
            "by_status": dict(
                AgentTask.objects.values_list("status").annotate(count=Count("id")).order_by()
            ),
        }

        agent_count = AgentProfile.objects.count()
        agents_by_status = dict(
            AgentProfile.objects.values_list("status").annotate(count=Count("id")).order_by()
        )

        return Response(
            {
                "companies": companies,
                "tasks": task_stats,
                "agents": {
                    "total": agent_count,
                    "by_status": agents_by_status,
                },
            }
        )
