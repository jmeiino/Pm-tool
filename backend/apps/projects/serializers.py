from rest_framework import serializers

from .models import Comment, Issue, Label, Project, Sprint


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ["id", "name", "color"]


class ProjectSerializer(serializers.ModelSerializer):
    issue_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Project
        fields = [
            "id", "name", "key", "description", "status",
            "is_synced", "jira_project_key", "issue_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sprint
        fields = [
            "id", "project", "name", "goal", "start_date", "end_date",
            "status", "jira_sprint_id", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.__str__", read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id", "issue", "author", "author_name", "body",
            "created_at", "updated_at",
        ]
        read_only_fields = ["author", "created_at", "updated_at"]


class IssueCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = [
            "id", "key", "project", "title", "description", "issue_type",
            "priority", "assignee", "sprint", "parent",
            "story_points", "due_date", "labels",
        ]
        read_only_fields = ["key"]

    def create(self, validated_data):
        labels = validated_data.pop("labels", [])
        issue = Issue.objects.create(**validated_data)
        if labels:
            issue.labels.set(labels)
        return issue


class IssueListSerializer(serializers.ModelSerializer):
    project_key = serializers.CharField(source="project.key", read_only=True)
    assignee_name = serializers.CharField(source="assignee.__str__", read_only=True, default=None)
    label_names = serializers.SlugRelatedField(
        source="labels", slug_field="name", many=True, read_only=True
    )

    class Meta:
        model = Issue
        fields = [
            "id", "key", "title", "issue_type", "status", "priority",
            "assignee", "assignee_name", "project", "project_key",
            "sprint", "story_points", "due_date", "label_names",
            "created_at", "updated_at",
        ]


class IssueDetailSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    labels = LabelSerializer(many=True, read_only=True)
    subtasks = IssueListSerializer(many=True, read_only=True)

    class Meta:
        model = Issue
        fields = [
            "id", "key", "title", "description", "issue_type", "status",
            "priority", "assignee", "reporter", "project", "sprint",
            "parent", "story_points", "due_date", "labels", "comments",
            "subtasks", "jira_issue_key", "jira_updated_at", "metadata",
            "created_at", "updated_at",
        ]
        read_only_fields = ["key", "created_at", "updated_at"]
