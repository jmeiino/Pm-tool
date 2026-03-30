"""Celery-Tasks fuer die Paperclip-Integration."""

import logging
import uuid

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_to_paperclip_task(self, issue_id: int, user_id: int, instructions: str = ""):
    """Issue asynchron an Paperclip delegieren."""
    from django.contrib.auth import get_user_model

    from apps.agents.models import AgentCompanyConfig, AgentMessage, AgentTask
    from apps.agents.services import AgentBridgeService
    from apps.projects.models import Issue

    User = get_user_model()

    try:
        issue = Issue.objects.select_related("project").get(id=issue_id)
        user = User.objects.get(id=user_id)
    except (Issue.DoesNotExist, User.DoesNotExist) as e:
        logger.error("Issue oder User nicht gefunden: %s", e)
        return {"status": "error", "reason": str(e)}

    company = AgentCompanyConfig.objects.filter(user=user, is_enabled=True).first()
    if not company:
        logger.warning("Keine aktive Agent-Company fuer User %s", user.username)
        return {"status": "error", "reason": "Keine Agent-Company konfiguriert"}

    # Duplikat-Pruefung
    existing = AgentTask.objects.filter(
        issue=issue,
        status__in=["pending", "assigned", "in_progress", "review", "needs_input"],
    ).exists()
    if existing:
        logger.info("Issue %s hat bereits einen aktiven Agent-Task", issue.key)
        return {"status": "skipped", "reason": "Aktiver Task existiert bereits"}

    task = AgentTask.objects.create(
        issue=issue,
        company=company,
        external_task_id=f"pm-{issue.key}-{uuid.uuid4().hex[:8]}",
        priority=3,
        task_type=_infer_task_type(issue),
    )

    AgentMessage.objects.create(
        task=task,
        message_type=AgentMessage.MessageType.SYSTEM,
        content=f"Aufgabe '{issue.title}' automatisch an Paperclip delegiert.",
    )

    try:
        bridge = AgentBridgeService(company)
        result = bridge.delegate_task(task, instructions=instructions)
        task.status = AgentTask.Status.ASSIGNED
        task.save(update_fields=["status", "updated_at"])
        logger.info("Issue %s erfolgreich an Paperclip delegiert", issue.key)
        return {"status": "ok", "task_id": task.id}
    except Exception as exc:
        AgentMessage.objects.create(
            task=task,
            message_type=AgentMessage.MessageType.ERROR,
            content=f"Verbindungsfehler: {str(exc)}",
        )
        logger.error("Delegation fehlgeschlagen: %s", exc)
        raise self.retry(exc=exc)


def _infer_task_type(issue) -> str:
    """Task-Typ anhand des Issue-Typs ableiten."""
    mapping = {
        "bug": "software",
        "feature": "software",
        "story": "software",
        "task": "general",
        "documentation": "content",
        "research": "research",
        "design": "design",
    }
    return mapping.get(issue.issue_type, "general")
