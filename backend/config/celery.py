import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("pmtool")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """Periodische Tasks für Integration-Syncs registrieren."""

    # Jira-Sync alle 15 Minuten
    sender.add_periodic_task(
        crontab(minute="*/15"),
        dispatch_integration_sync.s("jira"),
        name="jira-sync-every-15min",
    )

    # Confluence-Sync alle 30 Minuten
    sender.add_periodic_task(
        crontab(minute="*/30"),
        dispatch_integration_sync.s("confluence"),
        name="confluence-sync-every-30min",
    )

    # GitHub-Sync alle 10 Minuten
    sender.add_periodic_task(
        crontab(minute="*/10"),
        dispatch_integration_sync.s("github"),
        name="github-sync-every-10min",
    )

    # Microsoft-Kalender-Sync alle 15 Minuten
    sender.add_periodic_task(
        crontab(minute="*/15"),
        dispatch_integration_sync.s("microsoft_calendar"),
        name="microsoft-calendar-sync-every-15min",
    )


@app.task
def dispatch_integration_sync(integration_type: str):
    """Sync für alle aktiven Integrationen eines Typs auslösen."""
    from apps.integrations.models import IntegrationConfig

    integrations = IntegrationConfig.objects.filter(
        integration_type=integration_type,
        is_enabled=True,
        sync_status=IntegrationConfig.SyncStatus.IDLE,
    )

    for integration in integrations:
        integration.sync_status = IntegrationConfig.SyncStatus.SYNCING
        integration.save(update_fields=["sync_status", "updated_at"])

        if integration_type == "jira":
            from apps.integrations.jira.tasks import poll_jira_updates
            poll_jira_updates.delay(integration.id)
        elif integration_type == "confluence":
            from apps.integrations.confluence.tasks import poll_confluence_updates
            poll_confluence_updates.delay(integration.id)
        elif integration_type == "github":
            from apps.integrations.git.tasks import poll_github_updates
            poll_github_updates.delay(integration.id)
        elif integration_type == "microsoft_calendar":
            from apps.integrations.microsoft.tasks import poll_microsoft_calendar
            poll_microsoft_calendar.delay(integration.id)
