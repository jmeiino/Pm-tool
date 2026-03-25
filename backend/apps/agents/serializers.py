from rest_framework import serializers

from .models import AgentCompanyConfig, AgentMessage, AgentProfile, AgentTask


class AgentProfileSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AgentProfile
        fields = [
            "id",
            "external_id",
            "name",
            "role",
            "role_display",
            "department",
            "avatar_color",
            "capabilities",
            "ai_provider",
            "status",
            "status_display",
        ]
        read_only_fields = fields


class AgentMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_type = serializers.SerializerMethodField()
    sender_avatar_color = serializers.SerializerMethodField()

    class Meta:
        model = AgentMessage
        fields = [
            "id",
            "task",
            "sender_agent",
            "sender_user",
            "sender_name",
            "sender_type",
            "sender_avatar_color",
            "message_type",
            "content",
            "metadata",
            "is_decision_pending",
            "parent_message",
            "created_at",
        ]
        read_only_fields = ["task", "sender_agent", "sender_user", "created_at"]

    def get_sender_name(self, obj):
        if obj.sender_agent:
            return obj.sender_agent.name
        if obj.sender_user:
            return obj.sender_user.get_full_name() or obj.sender_user.username
        return "System"

    def get_sender_type(self, obj):
        if obj.sender_agent:
            return "agent"
        if obj.sender_user:
            return "user"
        return "system"

    def get_sender_avatar_color(self, obj):
        if obj.sender_agent:
            return obj.sender_agent.avatar_color
        return "#6B7280"


class AgentTaskListSerializer(serializers.ModelSerializer):
    issue_key = serializers.CharField(source="issue.key", read_only=True)
    issue_title = serializers.CharField(source="issue.title", read_only=True)
    assigned_agent_name = serializers.CharField(
        source="assigned_agent.name", read_only=True, default=None
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    message_count = serializers.IntegerField(read_only=True, default=0)
    pending_decisions = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = AgentTask
        fields = [
            "id",
            "issue",
            "issue_key",
            "issue_title",
            "external_task_id",
            "status",
            "status_display",
            "assigned_agent",
            "assigned_agent_name",
            "priority",
            "task_type",
            "result_summary",
            "deliverables",
            "estimated_completion",
            "message_count",
            "pending_decisions",
            "created_at",
            "updated_at",
        ]


class AgentTaskDetailSerializer(AgentTaskListSerializer):
    messages = AgentMessageSerializer(many=True, read_only=True)
    assigned_agent = AgentProfileSerializer(read_only=True)

    class Meta(AgentTaskListSerializer.Meta):
        fields = AgentTaskListSerializer.Meta.fields + ["messages"]


class DelegateTaskSerializer(serializers.Serializer):
    issue_id = serializers.IntegerField()
    priority = serializers.IntegerField(default=3, min_value=1, max_value=5)
    task_type = serializers.ChoiceField(
        choices=["software", "content", "design", "research", "general"],
        default="general",
    )
    instructions = serializers.CharField(required=False, allow_blank=True)


class ReplySerializer(serializers.Serializer):
    content = serializers.CharField()
    decision_option = serializers.CharField(required=False, allow_blank=True)


class AgentCompanyConfigSerializer(serializers.ModelSerializer):
    agent_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = AgentCompanyConfig
        fields = [
            "id",
            "name",
            "base_url",
            "is_enabled",
            "settings",
            "agent_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {
            "api_key": {"write_only": True},
            "webhook_secret": {"write_only": True},
        }
