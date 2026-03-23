from rest_framework import serializers

from .models import CalendarEvent, ConfluencePage, GitActivity, GitRepoAnalysis, IntegrationConfig, SyncLog


class IntegrationConfigSerializer(serializers.ModelSerializer):
    integration_type_display = serializers.CharField(source="get_integration_type_display", read_only=True)
    sync_status_display = serializers.CharField(source="get_sync_status_display", read_only=True)

    class Meta:
        model = IntegrationConfig
        fields = [
            "id",
            "integration_type",
            "integration_type_display",
            "is_enabled",
            "credentials",
            "settings",
            "last_synced_at",
            "sync_status",
            "sync_status_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "last_synced_at", "sync_status"]
        extra_kwargs = {
            "credentials": {"write_only": True},
        }


class SyncLogSerializer(serializers.ModelSerializer):
    direction_display = serializers.CharField(source="get_direction_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SyncLog
        fields = [
            "id",
            "integration",
            "direction",
            "direction_display",
            "status",
            "status_display",
            "records_processed",
            "records_created",
            "records_updated",
            "errors",
            "started_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = fields


class ConfluencePageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfluencePage
        fields = [
            "id",
            "confluence_page_id",
            "space_key",
            "title",
            "content_text",
            "last_confluence_update",
            "ai_summary",
            "ai_action_items",
            "ai_decisions",
            "ai_risks",
            "ai_processed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "ai_summary",
            "ai_action_items",
            "ai_decisions",
            "ai_risks",
            "ai_processed_at",
        ]


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = [
            "id",
            "external_id",
            "title",
            "start_time",
            "end_time",
            "is_all_day",
            "location",
            "attendees",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class GitRepoAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitRepoAnalysis
        fields = [
            "id",
            "repo_full_name",
            "description",
            "primary_language",
            "languages",
            "stars",
            "forks",
            "open_issues_count",
            "topics",
            "default_branch",
            "readme_content",
            "recent_commits_summary",
            "ai_summary",
            "ai_tech_stack",
            "ai_strengths",
            "ai_improvements",
            "ai_action_items",
            "ai_processed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "description",
            "primary_language",
            "languages",
            "stars",
            "forks",
            "open_issues_count",
            "topics",
            "default_branch",
            "readme_content",
            "recent_commits_summary",
            "ai_summary",
            "ai_tech_stack",
            "ai_strengths",
            "ai_improvements",
            "ai_action_items",
            "ai_processed_at",
            "created_at",
            "updated_at",
        ]


class GitActivitySerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)

    class Meta:
        model = GitActivity
        fields = [
            "id",
            "project",
            "event_type",
            "event_type_display",
            "author",
            "title",
            "description",
            "url",
            "external_id",
            "event_date",
            "linked_issue",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
