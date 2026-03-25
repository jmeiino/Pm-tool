"""Webhook-Handler für eingehende Events vom Agent-Service."""

import hashlib
import hmac
import json
import logging

from .models import AgentCompanyConfig, AgentMessage, AgentProfile, AgentTask

logger = logging.getLogger(__name__)


def verify_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """HMAC-SHA256 Signatur verifizieren."""
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def process_webhook_event(event_data: dict, company: AgentCompanyConfig) -> dict:
    """Webhook-Event verarbeiten und in DB speichern."""
    event_type = event_data.get("event_type", "")
    task_id = event_data.get("task_id", "")
    payload = event_data.get("payload", {})

    handler = EVENT_HANDLERS.get(event_type)
    if not handler:
        logger.warning("Unbekannter Event-Typ: %s", event_type)
        return {"status": "ignored", "reason": f"Unknown event type: {event_type}"}

    return handler(task_id, payload, company)


def _handle_agent_message(task_id: str, payload: dict, company: AgentCompanyConfig) -> dict:
    """Agent-Nachricht verarbeiten."""
    try:
        task = AgentTask.objects.get(external_task_id=task_id, company=company)
    except AgentTask.DoesNotExist:
        return {"status": "error", "reason": f"Task {task_id} not found"}

    sender_agent = None
    sender_agent_id = payload.get("sender_agent_id")
    if sender_agent_id:
        sender_agent, _ = AgentProfile.objects.get_or_create(
            external_id=sender_agent_id,
            defaults={
                "company": company,
                "name": payload.get("sender_name", sender_agent_id),
                "role": payload.get("sender_role", "specialist"),
                "department": payload.get("sender_department", ""),
                "avatar_color": payload.get("sender_avatar_color", "#6366F1"),
            },
        )

    message = AgentMessage.objects.create(
        task=task,
        sender_agent=sender_agent,
        message_type=payload.get("message_type", "text"),
        content=payload.get("content", ""),
        metadata=payload.get("metadata", {}),
        is_decision_pending=payload.get("message_type") == "question",
    )

    # Redis Pub/Sub für SSE
    _publish_to_stream(task.external_task_id, {
        "type": "new_message",
        "message": {
            "id": message.id,
            "sender_name": sender_agent.name if sender_agent else "System",
            "sender_type": "agent",
            "message_type": message.message_type,
            "content": message.content,
            "metadata": message.metadata,
            "is_decision_pending": message.is_decision_pending,
            "created_at": message.created_at.isoformat(),
        },
    })

    return {"status": "ok", "message_id": message.id}


def _handle_task_status_changed(task_id: str, payload: dict, company: AgentCompanyConfig) -> dict:
    """Task-Status aktualisieren."""
    try:
        task = AgentTask.objects.get(external_task_id=task_id, company=company)
    except AgentTask.DoesNotExist:
        return {"status": "error", "reason": f"Task {task_id} not found"}

    new_status = payload.get("status", "")
    if new_status and new_status in dict(AgentTask.Status.choices):
        old_status = task.status
        task.status = new_status
        update_fields = ["status", "updated_at"]

        if new_status == "completed":
            task.result_summary = payload.get("result_summary", "")
            update_fields.append("result_summary")

        if payload.get("assigned_agent_id"):
            agent = AgentProfile.objects.filter(
                external_id=payload["assigned_agent_id"]
            ).first()
            if agent:
                task.assigned_agent = agent
                update_fields.append("assigned_agent")

        task.save(update_fields=update_fields)

        # System-Message erstellen
        AgentMessage.objects.create(
            task=task,
            message_type=AgentMessage.MessageType.STATUS_CHANGE,
            content=f"Status: {old_status} → {new_status}",
            metadata={"old_status": old_status, "new_status": new_status},
        )

        _publish_to_stream(task.external_task_id, {
            "type": "status_changed",
            "old_status": old_status,
            "new_status": new_status,
        })

    return {"status": "ok"}


def _handle_task_deliverable(task_id: str, payload: dict, company: AgentCompanyConfig) -> dict:
    """Ergebnis/Deliverable speichern."""
    try:
        task = AgentTask.objects.get(external_task_id=task_id, company=company)
    except AgentTask.DoesNotExist:
        return {"status": "error", "reason": f"Task {task_id} not found"}

    deliverable = payload.get("deliverable", {})
    if deliverable:
        deliverables = task.deliverables or []
        deliverables.append(deliverable)
        task.deliverables = deliverables
        task.save(update_fields=["deliverables", "updated_at"])

    AgentMessage.objects.create(
        task=task,
        sender_agent=AgentProfile.objects.filter(
            external_id=payload.get("sender_agent_id", "")
        ).first(),
        message_type=AgentMessage.MessageType.DELIVERABLE,
        content=payload.get("content", "Neues Ergebnis bereitgestellt."),
        metadata={"deliverable": deliverable},
    )

    _publish_to_stream(task.external_task_id, {
        "type": "deliverable",
        "deliverable": deliverable,
    })

    return {"status": "ok"}


def _handle_agent_status_changed(task_id: str, payload: dict, company: AgentCompanyConfig) -> dict:
    """Agent-Status aktualisieren."""
    agent_id = payload.get("agent_id", "")
    new_status = payload.get("status", "")

    if agent_id and new_status:
        AgentProfile.objects.filter(
            external_id=agent_id, company=company
        ).update(status=new_status)

    return {"status": "ok"}


def _publish_to_stream(task_id: str, data: dict):
    """Event per Redis Pub/Sub an SSE-Stream senden."""
    try:
        import redis

        r = redis.from_url("redis://redis:6379/1")
        r.publish(f"agent_task:{task_id}", json.dumps(data))
    except Exception:
        logger.warning("Redis Pub/Sub nicht verfügbar, SSE-Event nicht gesendet")


EVENT_HANDLERS = {
    "agent.message": _handle_agent_message,
    "task.accepted": _handle_task_status_changed,
    "task.assigned": _handle_task_status_changed,
    "task.status_changed": _handle_task_status_changed,
    "task.needs_input": _handle_agent_message,
    "task.deliverable": _handle_task_deliverable,
    "task.completed": _handle_task_status_changed,
    "task.failed": _handle_task_status_changed,
    "agent.status_changed": _handle_agent_status_changed,
}
