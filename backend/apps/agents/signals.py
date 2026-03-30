"""Signals fuer automatische Paperclip-Delegation."""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.projects.models import Issue

logger = logging.getLogger(__name__)

AI_DELEGATION_LABELS = {"ai-agent", "paperclip", "auto-delegate"}


@receiver(post_save, sender=Issue)
def auto_delegate_to_paperclip(sender, instance, created, **kwargs):
    """Bei neuen Issues mit AI-Label automatisch an Paperclip delegieren."""
    if not created:
        return

    # Pruefe ob Issue AI-Labels hat
    issue_labels = set(instance.labels.values_list("name", flat=True))
    if not issue_labels & AI_DELEGATION_LABELS:
        return

    # Pruefe ob der Projekt-Owner auto_delegate aktiviert hat
    from apps.agents.models import AgentCompanyConfig

    company = AgentCompanyConfig.objects.filter(
        user=instance.project.owner,
        is_enabled=True,
    ).first()

    if not company:
        return

    if not company.settings.get("auto_delegate", False):
        return

    from apps.agents.tasks import send_to_paperclip_task

    send_to_paperclip_task.delay(
        issue_id=instance.id,
        user_id=instance.project.owner_id,
    )
    logger.info("Auto-Delegation ausgeloest fuer Issue %s", instance.key)
