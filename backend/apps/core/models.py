from django.db import models


class TimeStampedModel(models.Model):
    """Abstrakte Basisklasse mit created_at und updated_at Feldern."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
