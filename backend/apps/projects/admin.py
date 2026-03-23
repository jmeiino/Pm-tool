from django.contrib import admin

from .models import Comment, Issue, Label, Project, Sprint


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "status", "is_synced", "jira_project_key")
    list_filter = ("status", "is_synced")
    search_fields = ("name", "key")


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "status", "start_date", "end_date")
    list_filter = ("status", "project")


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("key", "title", "issue_type", "status", "priority", "assignee")
    list_filter = ("issue_type", "status", "priority", "project")
    search_fields = ("title", "key")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("issue", "author", "created_at")


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
