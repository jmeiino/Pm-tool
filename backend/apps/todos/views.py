from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DailyPlan, DailyPlanItem, PersonalTodo, WeeklyPlan
from .serializers import (
    DailyPlanItemCreateSerializer,
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
        return DailyPlan.objects.filter(user=self.request.user).prefetch_related("items__todo")

    def retrieve(self, request, *args, **kwargs):
        """Tagesplan abrufen — erstellt automatisch einen leeren Plan falls keiner existiert."""
        date = kwargs.get("date")
        plan, _created = DailyPlan.objects.get_or_create(
            user=request.user,
            date=date,
        )
        serializer = self.get_serializer(
            self.get_queryset().get(pk=plan.pk)
        )
        return Response(serializer.data)

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
            DailyPlanItem.objects.filter(id=item_data["id"], daily_plan=daily_plan).update(order=item_data["order"])
        return Response(self.get_serializer(daily_plan).data)

    @action(detail=True, methods=["post"], url_path="add-item")
    def add_item(self, request, date=None):
        """Aufgabe zum Tagesplan hinzufügen."""
        daily_plan = self.get_object()
        serializer = DailyPlanItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        max_order = daily_plan.items.count()
        serializer.save(
            daily_plan=daily_plan,
            order=serializer.validated_data.get("order", max_order),
        )
        daily_plan.refresh_from_db()
        return Response(
            self.get_serializer(self.get_queryset().get(pk=daily_plan.pk)).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="remove-item")
    def remove_item(self, request, date=None):
        """Aufgabe aus dem Tagesplan entfernen."""
        daily_plan = self.get_object()
        item_id = request.data.get("item_id")
        if not item_id:
            return Response(
                {"detail": "item_id ist erforderlich."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        DailyPlanItem.objects.filter(id=item_id, daily_plan=daily_plan).delete()
        daily_plan.refresh_from_db()
        return Response(self.get_serializer(self.get_queryset().get(pk=daily_plan.pk)).data)

    @action(detail=True, methods=["post"], url_path="ai-suggest")
    def ai_suggest(self, request, date=None):
        """KI-gestützte Vorschläge für den Tagesplan generieren."""
        daily_plan = self.get_object()

        try:
            from apps.ai.client import get_ai_client
            from apps.ai.services import AIService
            from apps.integrations.models import CalendarEvent
            from apps.integrations.serializers import CalendarEventSerializer

            # Prüfen ob ein KI-Provider konfiguriert ist
            try:
                get_ai_client(user=request.user)
            except Exception:
                return Response(
                    {"detail": "Kein KI-Provider konfiguriert. Bitte in den Einstellungen einen API-Key hinterlegen."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            todos = PersonalTodo.objects.filter(user=request.user, status__in=["pending", "in_progress"])
            if not todos.exists():
                return Response(
                    {"detail": "Keine offenen Aufgaben vorhanden. Erstelle zuerst Aufgaben."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            calendar_events = CalendarEvent.objects.filter(
                user=request.user,
                start_time__date=daily_plan.date,
            )

            todos_data = PersonalTodoSerializer(todos, many=True).data
            events_data = CalendarEventSerializer(calendar_events, many=True).data

            service = AIService()
            result = service.suggest_daily_plan(
                todos=todos_data,
                calendar_events=events_data,
                capacity_hours=float(daily_plan.capacity_hours),
            )

            # Apply AI suggestion: create/update DailyPlanItems
            DailyPlanItem.objects.filter(daily_plan=daily_plan).delete()
            for i, block in enumerate(result.get("time_blocks", [])):
                todo = _match_todo_to_block(block, todos)
                if todo:
                    DailyPlanItem.objects.create(
                        daily_plan=daily_plan,
                        todo=todo,
                        order=i,
                        scheduled_start=block.get("start"),
                        time_block_minutes=_calc_minutes(block.get("start"), block.get("end")),
                        ai_reasoning=block.get("description", ""),
                    )

            daily_plan.ai_reasoning = result.get("reasoning", "")
            daily_plan.ai_summary = result.get("summary", "")
            daily_plan.save(update_fields=["ai_reasoning", "ai_summary", "updated_at"])

            return Response(self.get_serializer(daily_plan).data)
        except Exception as e:
            return Response(
                {"detail": f"KI-Vorschlag fehlgeschlagen: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class WeeklyPlanViewSet(viewsets.ModelViewSet):
    serializer_class = WeeklyPlanSerializer
    lookup_field = "week_start"

    def get_queryset(self):
        return WeeklyPlan.objects.filter(user=self.request.user).prefetch_related("daily_plans__items__todo")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def _match_todo_to_block(block: dict, todos) -> PersonalTodo | None:
    """Match an AI-suggested block to an actual todo."""
    # Try matching by ID first (if AI includes it)
    todo_id = block.get("todo_id")
    if todo_id:
        try:
            return todos.get(id=todo_id)
        except PersonalTodo.DoesNotExist:
            pass

    # Fuzzy match by title
    block_title = block.get("title", "").lower().strip()
    if not block_title:
        return None

    for todo in todos:
        if todo.title.lower().strip() == block_title:
            return todo

    # Substring match
    for todo in todos:
        if block_title in todo.title.lower() or todo.title.lower() in block_title:
            return todo

    return None


def _calc_minutes(start_str: str | None, end_str: str | None) -> int | None:
    """Calculate duration in minutes between two time strings."""
    if not start_str or not end_str:
        return None
    try:
        from datetime import datetime

        fmt = "%H:%M"
        start = datetime.strptime(start_str, fmt)
        end = datetime.strptime(end_str, fmt)
        delta = end - start
        return max(int(delta.total_seconds() / 60), 0)
    except (ValueError, TypeError):
        return None
