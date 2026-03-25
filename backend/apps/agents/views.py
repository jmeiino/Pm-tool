"""Views für die Agent-Integration: Tasks, Webhooks, SSE."""

import json
import logging
import uuid

from django.db.models import Count, Q
from django.http import StreamingHttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.projects.models import Issue

from .models import AgentCompanyConfig, AgentMessage, AgentProfile, AgentTask
from .serializers import (
    AgentProfileSerializer,
    AgentTaskDetailSerializer,
    AgentTaskListSerializer,
    DelegateTaskSerializer,
    ReplySerializer,
)
from .services import AgentBridgeService
from .webhook_handler import process_webhook_event, verify_webhook_signature

logger = logging.getLogger(__name__)


class AgentTaskViewSet(viewsets.ModelViewSet):
    """CRUD + Aktionen für Agent-Tasks."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            AgentTask.objects.filter(company__user=self.request.user)
            .select_related("issue", "assigned_agent", "company")
            .annotate(
                message_count=Count("messages"),
                pending_decisions=Count(
                    "messages", filter=Q(messages__is_decision_pending=True)
                ),
            )
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AgentTaskDetailSerializer
        return AgentTaskListSerializer

    @action(detail=False, methods=["post"])
    def delegate(self, request):
        """Neue Aufgabe an die agentische Firma delegieren."""
        serializer = DelegateTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        issue_id = serializer.validated_data["issue_id"]
        try:
            issue = Issue.objects.get(id=issue_id, project__owner=request.user)
        except Issue.DoesNotExist:
            return Response(
                {"detail": "Issue nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        company = AgentCompanyConfig.objects.filter(
            user=request.user, is_enabled=True
        ).first()
        if not company:
            return Response(
                {"detail": "Keine aktive Agent-Company konfiguriert."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Task erstellen
        task = AgentTask.objects.create(
            issue=issue,
            company=company,
            external_task_id=f"pm-{issue.key}-{uuid.uuid4().hex[:8]}",
            priority=serializer.validated_data.get("priority", 3),
            task_type=serializer.validated_data.get("task_type", "general"),
        )

        # System-Nachricht
        AgentMessage.objects.create(
            task=task,
            message_type=AgentMessage.MessageType.SYSTEM,
            content=f"Aufgabe '{issue.title}' an die agentische Firma delegiert.",
        )

        # An Agent-Service senden
        try:
            with AgentBridgeService(company) as bridge:
                bridge.delegate_task(
                    task,
                    instructions=serializer.validated_data.get("instructions", ""),
                )
            task.status = AgentTask.Status.ASSIGNED
            task.save(update_fields=["status", "updated_at"])
        except Exception as e:
            logger.error("Fehler beim Delegieren an Agent-Service: %s", e)
            AgentMessage.objects.create(
                task=task,
                message_type=AgentMessage.MessageType.ERROR,
                content=f"Verbindungsfehler zum Agent-Service: {str(e)}",
            )

        return Response(
            AgentTaskDetailSerializer(task).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def reply(self, request, pk=None):
        """User-Antwort auf Agent-Rückfrage senden."""
        task = self.get_object()
        serializer = ReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content = serializer.validated_data["content"]
        decision_option = serializer.validated_data.get("decision_option", "")

        # User-Message speichern
        message = AgentMessage.objects.create(
            task=task,
            sender_user=request.user,
            message_type=AgentMessage.MessageType.TEXT,
            content=content,
            metadata={"decision_option": decision_option} if decision_option else {},
        )

        # Offene Rückfragen als beantwortet markieren
        if decision_option:
            AgentMessage.objects.filter(
                task=task, is_decision_pending=True
            ).update(is_decision_pending=False)

        # An Agent-Service weiterleiten
        try:
            with AgentBridgeService(task.company) as bridge:
                bridge.send_reply(
                    task.external_task_id, content, decision_option
                )
        except Exception as e:
            logger.warning("Fehler beim Weiterleiten der Antwort: %s", e)

        return Response({"detail": "Antwort gesendet.", "message_id": message.id})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Aufgabe abbrechen."""
        task = self.get_object()

        if task.status in (AgentTask.Status.COMPLETED, AgentTask.Status.CANCELLED):
            return Response(
                {"detail": "Aufgabe ist bereits abgeschlossen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with AgentBridgeService(task.company) as bridge:
                bridge.cancel_task(task.external_task_id)
        except Exception:
            pass  # Abbruch trotzdem lokal durchführen

        task.status = AgentTask.Status.CANCELLED
        task.save(update_fields=["status", "updated_at"])

        AgentMessage.objects.create(
            task=task,
            message_type=AgentMessage.MessageType.SYSTEM,
            content="Aufgabe abgebrochen.",
        )

        return Response({"detail": "Aufgabe abgebrochen."})

    @action(detail=True, methods=["post"])
    def reprioritize(self, request, pk=None):
        """Priorität ändern."""
        task = self.get_object()
        new_priority = request.data.get("priority")
        if not new_priority or not isinstance(new_priority, int):
            return Response(
                {"detail": "priority (int) ist erforderlich."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task.priority = new_priority
        task.save(update_fields=["priority", "updated_at"])

        return Response({"detail": f"Priorität auf {new_priority} gesetzt."})


class AgentProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """Alle Agents der Firma anzeigen."""

    permission_classes = [IsAuthenticated]
    serializer_class = AgentProfileSerializer

    def get_queryset(self):
        return AgentProfile.objects.filter(company__user=self.request.user)


# ─── Webhook ──────────────────────────────────────────────────────────────────


@api_view(["POST"])
@permission_classes([AllowAny])
def webhook_event(request):
    """Webhook-Endpoint für Events vom Agent-Service."""
    signature = request.headers.get("X-Webhook-Signature", "")
    body = request.body

    # Company anhand der Signatur finden
    for company in AgentCompanyConfig.objects.filter(is_enabled=True):
        if verify_webhook_signature(body, signature, company.webhook_secret):
            try:
                event_data = json.loads(body)
                result = process_webhook_event(event_data, company)
                return Response(result)
            except json.JSONDecodeError:
                return Response(
                    {"detail": "Invalid JSON"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                logger.exception("Webhook-Fehler: %s", e)
                return Response(
                    {"detail": "Internal error"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

    return Response(
        {"detail": "Invalid signature"},
        status=status.HTTP_401_UNAUTHORIZED,
    )


# ─── SSE Stream ───────────────────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def task_stream(request, task_id):
    """Server-Sent Events Stream für Live-Updates eines Agent-Tasks."""
    try:
        task = AgentTask.objects.get(id=task_id, company__user=request.user)
    except AgentTask.DoesNotExist:
        return Response(
            {"detail": "Task nicht gefunden."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def event_generator():
        try:
            import redis

            r = redis.from_url("redis://redis:6379/1")
            pubsub = r.pubsub()
            pubsub.subscribe(f"agent_task:{task.external_task_id}")

            # Initial heartbeat
            yield "data: {\"type\": \"connected\"}\n\n"

            for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data'].decode()}\n\n"
        except Exception:
            yield "data: {\"type\": \"error\", \"message\": \"Stream nicht verfügbar\"}\n\n"

    response = StreamingHttpResponse(
        event_generator(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


# ─── Company Status ───────────────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def company_status(request):
    """Firmenstatus: Agent-Auslastung, aktive Tasks."""
    company = AgentCompanyConfig.objects.filter(
        user=request.user, is_enabled=True
    ).first()

    if not company:
        return Response({"detail": "Keine Agent-Company konfiguriert."}, status=404)

    agents = AgentProfile.objects.filter(company=company)
    active_tasks = AgentTask.objects.filter(
        company=company,
        status__in=["assigned", "in_progress", "review", "needs_input"],
    )

    return Response({
        "company_name": company.name,
        "agents": AgentProfileSerializer(agents, many=True).data,
        "active_task_count": active_tasks.count(),
        "pending_decisions": AgentMessage.objects.filter(
            task__company=company,
            is_decision_pending=True,
        ).count(),
    })
