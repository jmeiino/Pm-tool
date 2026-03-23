from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Label(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default="#6B7280")

    class Meta:
        verbose_name = "Label"
        verbose_name_plural = "Labels"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Aktiv"
        ARCHIVED = "archived", "Archiviert"
        PAUSED = "paused", "Pausiert"

    name = models.CharField(max_length=255)
    key = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_projects"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_synced = models.BooleanField(default=False, help_text="Wird mit Jira synchronisiert")
    jira_project_key = models.CharField(max_length=20, null=True, blank=True, unique=True)
    jira_project_id = models.CharField(max_length=50, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Projekt"
        verbose_name_plural = "Projekte"
        ordering = ["name"]

    def __str__(self):
        return f"{self.key} - {self.name}"


class Sprint(TimeStampedModel):
    class Status(models.TextChoices):
        PLANNED = "planned", "Geplant"
        ACTIVE = "active", "Aktiv"
        CLOSED = "closed", "Abgeschlossen"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="sprints")
    name = models.CharField(max_length=255)
    goal = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    jira_sprint_id = models.IntegerField(null=True, blank=True, unique=True)

    class Meta:
        verbose_name = "Sprint"
        verbose_name_plural = "Sprints"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.project.key} - {self.name}"


class Issue(TimeStampedModel):
    class IssueType(models.TextChoices):
        EPIC = "epic", "Epic"
        STORY = "story", "Story"
        TASK = "task", "Aufgabe"
        BUG = "bug", "Bug"
        SUBTASK = "subtask", "Unteraufgabe"

    class Priority(models.TextChoices):
        HIGHEST = "highest", "Höchste"
        HIGH = "high", "Hoch"
        MEDIUM = "medium", "Mittel"
        LOW = "low", "Niedrig"
        LOWEST = "lowest", "Niedrigste"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="issues")
    sprint = models.ForeignKey(
        Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name="issues"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="subtasks"
    )
    key = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    issue_type = models.CharField(max_length=20, choices=IssueType.choices, default=IssueType.TASK)
    status = models.CharField(max_length=50, default="to_do")
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_issues",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_issues",
    )
    story_points = models.IntegerField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    labels = models.ManyToManyField(Label, blank=True, related_name="issues")
    jira_issue_id = models.CharField(max_length=50, null=True, blank=True, unique=True)
    jira_issue_key = models.CharField(max_length=30, null=True, blank=True)
    jira_updated_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Issue"
        verbose_name_plural = "Issues"
        ordering = ["-updated_at"]

    def save(self, *args, **kwargs):
        if not self.key:
            next_seq = Issue.objects.filter(project=self.project).count() + 1
            self.key = f"{self.project.key}-{next_seq}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.key}: {self.title}"


class Comment(TimeStampedModel):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField()
    jira_comment_id = models.CharField(max_length=50, null=True, blank=True, unique=True)

    class Meta:
        verbose_name = "Kommentar"
        verbose_name_plural = "Kommentare"
        ordering = ["created_at"]

    def __str__(self):
        return f"Kommentar zu {self.issue.key} von {self.author}"
