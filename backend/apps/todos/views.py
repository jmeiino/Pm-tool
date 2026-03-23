from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DailyPlan, DailyPlanItem, PersonalTodo, WeeklyPlan
from .serializers import (
    DailyPlanSerializer,
    PersonalTodoSerializer,
    WeeklyPlanSerializer,
)


class PersonalTodoViewSet(viewsets.ModelViewSet):
    serializer_class = PersonalTodoSerializer
    filterset_fields = ["status", "source", "priority", "due_date"]
    search_fields = ["title", "description"]
    ordering_fields = ["priority", "due_date", "created_at", "updated_at"]

    def get_queryset(self):
        return PersonalTodo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DailyPlanViewSet(viewsets.ModelViewSet):
    serializer_class = DailyPlanSerializer
    lookup_field = "date"

    def get_queryset(self):
        return (
            DailyPlan.objects.filter(user=self.request.user)
            .prefetch_related("items__todo")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="reorder")
    def reorder(self, request, date=None):
        """Reihenfolge der Einträge im Tagesplan aktualisieren.

        Expects: {"items": [{"id": 1, "order": 0}, ...]}
        """
        daily_plan = self.get_object()
        items_data = request.data.get("items", [])
        for item_data in items_data:
            DailyPlanItem.objects.filter(
                id=item_data["id"], daily_plan=daily_plan
            ).update(order=item_data["order"])
        return Response(self.get_serializer(daily_plan).data)

    @action(detail=True, methods=["post"], url_path="ai-suggest")
    def ai_suggest(self, request, date=None):
        """KI-gestützte Vorschläge für den Tagesplan generieren.

        Placeholder – will be implemented with AI service integration.
        """
        daily_plan = self.get_object()
        return Response(
            {
                "detail": "KI-Vorschläge werden noch implementiert.",
                "plan": self.get_serializer(daily_plan).data,
            },
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class WeeklyPlanViewSet(viewsets.ModelViewSet):
    serializer_class = WeeklyPlanSerializer
    lookup_field = "week_start"

    def get_queryset(self):
        return (
            WeeklyPlan.objects.filter(user=self.request.user)
            .prefetch_related("daily_plans__items__todo")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
