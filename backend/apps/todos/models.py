from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class PersonalTodo(TimeStampedModel):
    class Priority(models.IntegerChoices):
        URGENT = 1, "Dringend"
        HIGH = 2, "Hoch"
        MEDIUM = 3, "Mittel"
        LOW = 4, "Niedrig"

    class Status(models.TextChoices):
        PENDING = "pending", "Ausstehend"
        IN_PROGRESS = "in_progress", "In Bearbeitung"
        DONE = "done", "Erledigt"
        CANCELLED = "cancelled", "Abgebrochen"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manuell"
        JIRA = "jira", "Jira"
        CONFLUENCE = "confluence", "Confluence"
        EMAIL = "email", "E-Mail"
        TEAMS = "teams", "Teams"
        AI = "ai", "KI"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="personal_todos")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    priority = models.IntegerField(choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)
    linked_issue = models.ForeignKey(
        "projects.Issue",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="personal_todos",
    )
    linked_confluence_page_id = models.CharField(max_length=50, null=True, blank=True)
    linked_email_id = models.CharField(max_length=255, null=True, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Aufgabe"
        verbose_name_plural = "Aufgaben"
        ordering = ["-priority", "due_date"]

    def __str__(self):
        return self.title


class DailyPlan(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_plans")
    date = models.DateField()
    ai_summary = models.TextField(blank=True)
    ai_reasoning = models.TextField(blank=True)
    capacity_hours = models.DecimalField(max_digits=5, decimal_places=2, default=8.00)

    class Meta:
        unique_together = ("user", "date")
        verbose_name = "Tagesplan"
        verbose_name_plural = "Tagespläne"
        ordering = ["-date"]

    def __str__(self):
        return f"Tagesplan {self.date} – {self.user}"


class DailyPlanItem(TimeStampedModel):
    daily_plan = models.ForeignKey(DailyPlan, on_delete=models.CASCADE, related_name="items")
    todo = models.ForeignKey(PersonalTodo, on_delete=models.CASCADE, related_name="plan_items")
    order = models.IntegerField()
    scheduled_start = models.TimeField(null=True, blank=True)
    time_block_minutes = models.IntegerField(null=True, blank=True)
    ai_reasoning = models.TextField(blank=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("daily_plan", "todo")
        verbose_name = "Tagesplan-Eintrag"
        verbose_name_plural = "Tagesplan-Einträge"

    def __str__(self):
        return f"#{self.order} {self.todo.title}"


class WeeklyPlan(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weekly_plans")
    week_start = models.DateField()
    daily_plans = models.ManyToManyField(DailyPlan, blank=True, related_name="weekly_plans")
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "week_start")
        verbose_name = "Wochenplan"
        verbose_name_plural = "Wochenpläne"
        ordering = ["-week_start"]

    def __str__(self):
        return f"Wochenplan ab {self.week_start} – {self.user}"
