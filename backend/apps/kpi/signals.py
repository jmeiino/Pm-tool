from __future__ import annotations

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .client import track_kpi

logger = logging.getLogger(__name__)


def connect_issue_signals(issue_model):
    """Call from AppConfig.ready() with the Issue model class."""
    @receiver(post_save, sender=issue_model)
    def track_issue_event(sender, instance, created, **kwargs):
        if created:
            track_kpi(
                event_type="project.issue_created",
                category="usage",
                kpi_id="usage.issue_created",
                value=1,
                dimensions={
                    "project_id": str(getattr(instance, "project_id", "")),
                    "issue_type": getattr(instance, "issue_type", "unknown"),
                    "priority": getattr(instance, "priority", "medium"),
                },
            )
        elif getattr(instance, "status", None) == "done":
            track_kpi(
                event_type="project.issue_completed",
                category="business_impact",
                kpi_id="business_impact.issue_completion",
                value=1,
                dimensions={
                    "project_id": str(getattr(instance, "project_id", "")),
                    "issue_id": str(instance.pk),
                    "duration_days": getattr(instance, "duration_days", 0),
                },
            )
