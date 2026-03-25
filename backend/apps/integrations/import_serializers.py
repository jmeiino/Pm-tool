"""Serializer für Import-Preview und -Confirm Endpoints."""

from rest_framework import serializers

# ─── Jira Preview ────────────────────────────────────────────────────────────

class JiraPreviewIssueSerializer(serializers.Serializer):
    jira_id = serializers.CharField()
    key = serializers.CharField()
    summary = serializers.CharField()
    status = serializers.CharField(allow_null=True)
    assignee = serializers.CharField(allow_null=True)
    sprint = serializers.CharField(allow_null=True)
    issue_type = serializers.CharField(allow_null=True)
    priority = serializers.CharField(allow_null=True)


class JiraPreviewProjectSerializer(serializers.Serializer):
    jira_id = serializers.CharField()
    key = serializers.CharField()
    name = serializers.CharField()
    issues = JiraPreviewIssueSerializer(many=True)


class JiraPreviewResponseSerializer(serializers.Serializer):
    projects = JiraPreviewProjectSerializer(many=True)
    available_assignees = serializers.ListField(child=serializers.CharField())
    available_statuses = serializers.ListField(child=serializers.CharField())
    available_sprints = serializers.ListField(child=serializers.CharField())


# ─── Jira Confirm ────────────────────────────────────────────────────────────

class JiraConfirmProjectSerializer(serializers.Serializer):
    jira_project_id = serializers.CharField()
    jira_project_key = serializers.CharField()
    name = serializers.CharField()
    issue_ids = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class JiraConfirmRequestSerializer(serializers.Serializer):
    projects = JiraConfirmProjectSerializer(many=True)


# ─── GitHub Preview ──────────────────────────────────────────────────────────

class GitHubPreviewIssueSerializer(serializers.Serializer):
    github_id = serializers.IntegerField()
    number = serializers.IntegerField()
    title = serializers.CharField()
    state = serializers.CharField()
    assignee = serializers.CharField(allow_null=True)
    author = serializers.CharField(allow_null=True)
    labels = serializers.ListField(child=serializers.CharField())
    is_pull_request = serializers.BooleanField()


class GitHubPreviewRepoSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    description = serializers.CharField(allow_null=True)
    language = serializers.CharField(allow_null=True)
    stars = serializers.IntegerField()
    open_issues_count = serializers.IntegerField()
    issues = GitHubPreviewIssueSerializer(many=True)


class GitHubPreviewResponseSerializer(serializers.Serializer):
    repos = GitHubPreviewRepoSerializer(many=True)
    github_username = serializers.CharField()


# ─── GitHub Confirm ──────────────────────────────────────────────────────────

class GitHubConfirmRepoSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    target_project_id = serializers.IntegerField(required=False, allow_null=True)
    create_new_project = serializers.BooleanField(default=True)
    project_name = serializers.CharField(required=False, allow_blank=True)
    selected_issue_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)


class GitHubConfirmRequestSerializer(serializers.Serializer):
    repos = GitHubConfirmRepoSerializer(many=True)


# ─── Confluence Preview ──────────────────────────────────────────────────────

class ConfluencePreviewSpaceSerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)


class ConfluencePreviewPageSerializer(serializers.Serializer):
    confluence_page_id = serializers.CharField()
    title = serializers.CharField()
    space_key = serializers.CharField()
    author = serializers.CharField(allow_null=True)
    last_updated = serializers.CharField(allow_null=True)
    last_updated_by = serializers.CharField(allow_null=True)


class ConfluencePreviewResponseSerializer(serializers.Serializer):
    spaces = ConfluencePreviewSpaceSerializer(many=True, required=False)
    pages = ConfluencePreviewPageSerializer(many=True, required=False)


# ─── Confluence Confirm ──────────────────────────────────────────────────────

class ConfluenceConfirmPageSerializer(serializers.Serializer):
    confluence_page_id = serializers.CharField()
    space_key = serializers.CharField()
    title = serializers.CharField()
    analyze = serializers.BooleanField(default=False)


class ConfluenceConfirmRequestSerializer(serializers.Serializer):
    pages = ConfluenceConfirmPageSerializer(many=True)
    selected_action_item_indices = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )


# ─── Shared ──────────────────────────────────────────────────────────────────

class ImportConfirmResponseSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    detail = serializers.CharField()
