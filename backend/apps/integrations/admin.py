from django.contrib import admin

from .models import CalendarEvent, ConfluencePage, GitActivity, IntegrationConfig, SyncLog


@admin.register(IntegrationConfig)
class IntegrationConfigAdmin(admin.ModelAdmin):
    list_display = ("user", "integration_type", "is_enabled", "sync_status", "last_synced_at")
    list_filter = ("integration_type", "is_enabled", "sync_status")
    search_fields = ("user__email",)


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = (
        "integration",
        "direction",
        "status",
        "records_processed",
        "started_at",
        "completed_at",
    )
    list_filter = ("direction", "status")
    readonly_fields = ("errors",)


@admin.register(ConfluencePage)
class ConfluencePageAdmin(admin.ModelAdmin):
    list_display = ("title", "space_key", "confluence_page_id", "last_confluence_update", "ai_processed_at")
    list_filter = ("space_key",)
    search_fields = ("title", "content_text")


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "start_time", "end_time", "is_all_day")
    list_filter = ("is_all_day",)
    search_fields = ("title",)


@admin.register(GitActivity)
class GitActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "event_type", "author", "project", "event_date")
    list_filter = ("event_type", "project")
    search_fields = ("title", "author")
