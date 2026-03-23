from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "notification_type", "severity", "is_read", "created_at")
    list_filter = ("notification_type", "severity", "is_read")
    search_fields = ("title", "message", "user__username")
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_read",)
