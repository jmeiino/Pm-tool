"""Signals fuer automatische Paperclip-Delegation."""

import logging

from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from apps.projects.models import Issue

logger = logging.getLogger(__name__)

AI_DELEGATION_LABELS = {"ai-agent", "paperclip", "auto-delegate"}


@receiver(m2m_changed, sender=Issue.labels.through)
def auto_delegate_on_labels(sender, instance, action, **kwargs):
    """Nach Setzen von AI-Labels automatisch an Paperclip delegieren."""
    if action != "post_add":
        return

    issue_labels = set(instance.labels.values_list("name", flat=True))
    if not issue_labels & AI_DELEGATION_LABELS:
        return

    # Bereits delegiert?
    from apps.agents.models import AgentCompanyConfig, AgentTask

    if AgentTask.objects.filter(
        issue=instance,
        status__in=["pending", "assigned", "in_progress", "review"],
    ).exists():
        return

    company = AgentCompanyConfig.objects.filter(
        user=instance.project.owner,
        is_enabled=True,
    ).first()

    if not company or not company.settings.get("auto_delegate", False):
        return

    from apps.agents.tasks import send_to_paperclip_task

    send_to_paperclip_task.delay(
        issue_id=instance.id,
        user_id=instance.project.owner_id,
    )
    logger.info("Auto-Delegation ausgeloest fuer Issue %s", instance.key)
