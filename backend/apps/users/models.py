from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Erweitertes User-Model mit Präferenzen für das PM-Tool."""

    timezone = models.CharField(max_length=50, default="Europe/Berlin")
    daily_capacity_hours = models.DecimalField(
        max_digits=4, decimal_places=2, default=8.00
    )
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="UI-Präferenzen, Benachrichtigungseinstellungen etc.",
    )

    class Meta:
        verbose_name = "Benutzer"
        verbose_name_plural = "Benutzer"

    def __str__(self):
        return self.get_full_name() or self.username
