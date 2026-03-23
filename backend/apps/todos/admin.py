from django.contrib import admin

from .models import DailyPlan, DailyPlanItem, PersonalTodo, WeeklyPlan


class DailyPlanItemInline(admin.TabularInline):
    model = DailyPlanItem
    extra = 0
    ordering = ["order"]


@admin.register(PersonalTodo)
class PersonalTodoAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "priority", "status", "source", "due_date")
    list_filter = ("status", "priority", "source")
    search_fields = ("title", "description")
    raw_id_fields = ("user", "linked_issue")


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "capacity_hours")
    list_filter = ("date",)
    inlines = [DailyPlanItemInline]
    raw_id_fields = ("user",)


@admin.register(DailyPlanItem)
class DailyPlanItemAdmin(admin.ModelAdmin):
    list_display = ("daily_plan", "todo", "order", "scheduled_start", "time_block_minutes")
    list_filter = ("daily_plan__date",)
    raw_id_fields = ("daily_plan", "todo")


@admin.register(WeeklyPlan)
class WeeklyPlanAdmin(admin.ModelAdmin):
    list_display = ("week_start", "user")
    list_filter = ("week_start",)
    raw_id_fields = ("user",)
    filter_horizontal = ("daily_plans",)
