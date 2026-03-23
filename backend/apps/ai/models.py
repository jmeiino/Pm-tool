from django.db import models

from apps.core.models import TimeStampedModel


class AIResult(TimeStampedModel):
    class ResultType(models.TextChoices):
        SUMMARY = "summary", "Zusammenfassung"
        ACTION_ITEMS = "action_items", "Aktionspunkte"
        PRIORITIZATION = "prioritization", "Priorisierung"
        DAILY_PLAN = "daily_plan", "Tagesplan"
        EXTRACTION = "extraction", "Extraktion"

    content_hash = models.CharField(max_length=64, db_index=True)
    result_type = models.CharField(max_length=20, choices=ResultType.choices)
    input_preview = models.TextField(blank=True)
    result = models.JSONField()
    model_used = models.CharField(max_length=50)
    tokens_used = models.IntegerField(default=0)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "KI-Ergebnis"
        verbose_name_plural = "KI-Ergebnisse"

    def __str__(self):
        return f"{self.get_result_type_display()} ({self.content_hash[:8]})"
