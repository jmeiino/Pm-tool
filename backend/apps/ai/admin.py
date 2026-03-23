from django.contrib import admin

from .models import AIResult


@admin.register(AIResult)
class AIResultAdmin(admin.ModelAdmin):
    list_display = ("content_hash", "result_type", "model_used", "tokens_used", "expires_at", "created_at")
    list_filter = ("result_type", "model_used")
    search_fields = ("content_hash", "input_preview")
    readonly_fields = ("content_hash", "result", "created_at", "updated_at")
