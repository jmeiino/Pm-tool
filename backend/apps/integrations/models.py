from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class IntegrationConfig(TimeStampedModel):
    class IntegrationType(models.TextChoices):
        JIRA = "jira", "Jira"
        CONFLUENCE = "confluence", "Confluence"
        MICROSOFT_CALENDAR = "microsoft_calendar", "Microsoft Kalender"
        MICROSOFT_EMAIL = "microsoft_email", "Microsoft E-Mail"
        MICROSOFT_TEAMS = "microsoft_teams", "Microsoft Teams"
        MICROSOFT_TODO = "microsoft_todo", "Microsoft To Do"
        GITHUB = "github", "GitHub"

    class SyncStatus(models.TextChoices):
        IDLE = "idle", "Bereit"
        SYNCING = "syncing", "Synchronisiert"
        ERROR = "error", "Fehler"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="integrations",
    )
    integration_type = models.CharField(
        max_length=30,
        choices=IntegrationType.choices,
    )
    is_enabled = models.BooleanField(default=False)
    credentials = models.JSONField(
        default=dict,
        help_text="Verschlüsselte Zugangsdaten",
    )
    settings = models.JSONField(
        default=dict,
        help_text="poll_interval, selected_projects etc.",
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(
        max_length=10,
        choices=SyncStatus.choices,
        default=SyncStatus.IDLE,
    )

    class Meta:
        unique_together = ("user", "integration_type")
        verbose_name = "Integration"
        verbose_name_plural = "Integrationen"

    def __str__(self):
        return f"{self.user} - {self.get_integration_type_display()}"


class SyncLog(TimeStampedModel):
    class Direction(models.TextChoices):
        INBOUND = "inbound", "Eingehend"
        OUTBOUND = "outbound", "Ausgehend"
        BIDIRECTIONAL = "bidirectional", "Bidirektional"

    class Status(models.TextChoices):
        STARTED = "started", "Gestartet"
        COMPLETED = "completed", "Abgeschlossen"
        FAILED = "failed", "Fehlgeschlagen"

    integration = models.ForeignKey(
        IntegrationConfig,
        on_delete=models.CASCADE,
        related_name="sync_logs",
    )
    direction = models.CharField(
        max_length=15,
        choices=Direction.choices,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
    )
    records_processed = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    errors = models.JSONField(default=list)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Sync-Protokoll"
        verbose_name_plural = "Sync-Protokolle"

    def __str__(self):
        return f"{self.integration} - {self.started_at:%Y-%m-%d %H:%M}"


class ConfluencePage(TimeStampedModel):
    confluence_page_id = models.CharField(max_length=50, unique=True)
    space_key = models.CharField(max_length=20)
    title = models.CharField(max_length=500)
    content_text = models.TextField(blank=True)
    last_confluence_update = models.DateTimeField()
    ai_summary = models.TextField(blank=True)
    ai_action_items = models.JSONField(default=list)
    ai_decisions = models.JSONField(default=list)
    ai_risks = models.JSONField(default=list)
    ai_processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Confluence-Seite"
        verbose_name_plural = "Confluence-Seiten"

    def __str__(self):
        return self.title


class CalendarEvent(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_events",
    )
    external_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=500, blank=True)
    attendees = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Kalender-Termin"
        verbose_name_plural = "Kalender-Termine"

    def __str__(self):
        return f"{self.title} ({self.start_time:%Y-%m-%d %H:%M})"


class GitRepoAnalysis(TimeStampedModel):
    """Gespeicherte KI-Analyse eines GitHub-Repositories."""

    repo_full_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    primary_language = models.CharField(max_length=100, blank=True)
    languages = models.JSONField(default=dict)
    stars = models.IntegerField(default=0)
    forks = models.IntegerField(default=0)
    open_issues_count = models.IntegerField(default=0)
    topics = models.JSONField(default=list)
    default_branch = models.CharField(max_length=100, default="main")
    readme_content = models.TextField(blank=True)
    recent_commits_summary = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    ai_tech_stack = models.JSONField(default=list)
    ai_strengths = models.JSONField(default=list)
    ai_improvements = models.JSONField(default=list)
    ai_action_items = models.JSONField(default=list)
    ai_processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Repository-Analyse"
        verbose_name_plural = "Repository-Analysen"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.repo_full_name


class GitActivity(TimeStampedModel):
    class EventType(models.TextChoices):
        COMMIT = "commit", "Commit"
        PR_OPENED = "pr_opened", "PR geöffnet"
        PR_MERGED = "pr_merged", "PR gemerged"
        PR_CLOSED = "pr_closed", "PR geschlossen"
        PR_REVIEWED = "pr_reviewed", "PR reviewt"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="git_activities",
    )
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
    )
    author = models.CharField(max_length=255)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    external_id = models.CharField(max_length=255)
    event_date = models.DateTimeField()
    linked_issue = models.ForeignKey(
        "projects.Issue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="git_activities",
    )

    class Meta:
        verbose_name = "Git-Aktivität"
        verbose_name_plural = "Git-Aktivitäten"
        ordering = ["-event_date"]

    def __str__(self):
        return f"{self.get_event_type_display()}: {self.title}"
