from rest_framework import serializers

from .models import DailyPlan, DailyPlanItem, PersonalTodo, WeeklyPlan


class PersonalTodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalTodo
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "estimated_hours",
            "source",
            "linked_issue",
            "linked_confluence_page_id",
            "linked_email_id",
            "ai_confidence",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class DailyPlanItemSerializer(serializers.ModelSerializer):
    todo_title = serializers.CharField(source="todo.title", read_only=True)

    class Meta:
        model = DailyPlanItem
        fields = [
            "id",
            "todo",
            "todo_title",
            "order",
            "scheduled_start",
            "time_block_minutes",
            "ai_reasoning",
        ]


class DailyPlanItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPlanItem
        fields = [
            "todo",
            "order",
            "scheduled_start",
            "time_block_minutes",
        ]
        extra_kwargs = {
            "order": {"required": False},
        }


class DailyPlanSerializer(serializers.ModelSerializer):
    items = DailyPlanItemSerializer(many=True, read_only=True)

    class Meta:
        model = DailyPlan
        fields = [
            "id",
            "date",
            "ai_summary",
            "ai_reasoning",
            "capacity_hours",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class WeeklyPlanSerializer(serializers.ModelSerializer):
    daily_plans = DailyPlanSerializer(many=True, read_only=True)

    class Meta:
        model = WeeklyPlan
        fields = [
            "id",
            "week_start",
            "daily_plans",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
