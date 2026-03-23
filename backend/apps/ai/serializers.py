from rest_framework import serializers

from .models import AIResult


class AIResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIResult
        fields = [
            "id",
            "content_hash",
            "result_type",
            "input_preview",
            "result",
            "model_used",
            "tokens_used",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PrioritizeRequestSerializer(serializers.Serializer):
    todos = serializers.ListField(child=serializers.DictField(), help_text="Liste der zu priorisierenden Aufgaben")


class SummarizeRequestSerializer(serializers.Serializer):
    content = serializers.CharField(help_text="Zu zusammenfassender Inhalt")
    content_type = serializers.CharField(default="text", help_text="Art des Inhalts")


class ExtractActionsRequestSerializer(serializers.Serializer):
    text = serializers.CharField(help_text="Text, aus dem Aktionspunkte extrahiert werden")


class DailyPlanRequestSerializer(serializers.Serializer):
    todos = serializers.ListField(child=serializers.DictField(), help_text="Liste der Aufgaben")
    calendar_events = serializers.ListField(child=serializers.DictField(), default=list, help_text="Kalendereinträge")
    capacity_hours = serializers.FloatField(default=8.0, help_text="Verfügbare Stunden")


class AIResponseSerializer(serializers.Serializer):
    result = serializers.JSONField(help_text="KI-Ergebnis")
    cached = serializers.BooleanField(help_text="Ob das Ergebnis aus dem Cache stammt")
