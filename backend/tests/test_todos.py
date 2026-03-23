from datetime import date

import pytest

from tests.factories import DailyPlanFactory, PersonalTodoFactory, UserFactory


@pytest.mark.django_db
class TestTodoAPI:
    def test_create_todo(self, api_client, user):
        response = api_client.post(
            "/api/v1/todos/",
            {
                "title": "Neue Aufgabe",
                "priority": 2,
                "description": "Beschreibung",
            },
        )
        assert response.status_code == 201
        assert response.data["title"] == "Neue Aufgabe"
        assert response.data["priority"] == 2
        assert response.data["status"] == "pending"

    def test_list_todos_only_own(self, api_client, user):
        PersonalTodoFactory(user=user)
        PersonalTodoFactory(user=user)
        other_user = UserFactory()
        PersonalTodoFactory(user=other_user)

        response = api_client.get("/api/v1/todos/")
        assert response.status_code == 200
        assert response.data["count"] == 2

    def test_filter_todos_by_status(self, api_client, user):
        PersonalTodoFactory(user=user, status="pending")
        PersonalTodoFactory(user=user, status="done")

        response = api_client.get("/api/v1/todos/?status=pending")
        assert response.status_code == 200
        for todo in response.data["results"]:
            assert todo["status"] == "pending"

    def test_update_todo_status(self, api_client, user):
        todo = PersonalTodoFactory(user=user, status="pending")

        response = api_client.patch(
            f"/api/v1/todos/{todo.id}/",
            {
                "status": "done",
            },
        )
        assert response.status_code == 200
        assert response.data["status"] == "done"

    def test_delete_todo(self, api_client, user):
        todo = PersonalTodoFactory(user=user)

        response = api_client.delete(f"/api/v1/todos/{todo.id}/")
        assert response.status_code == 204

    def test_filter_todos_by_priority(self, api_client, user):
        PersonalTodoFactory(user=user, priority=1)
        PersonalTodoFactory(user=user, priority=3)

        response = api_client.get("/api/v1/todos/?priority=1")
        assert response.status_code == 200
        for todo in response.data["results"]:
            assert todo["priority"] == 1


@pytest.mark.django_db
class TestDailyPlanAPI:
    def test_create_daily_plan(self, api_client, user):
        today = date.today().isoformat()
        response = api_client.post(
            "/api/v1/daily-plans/",
            {
                "date": today,
            },
        )
        assert response.status_code == 201
        assert response.data["date"] == today

    def test_get_daily_plan_by_date(self, api_client, user):
        plan = DailyPlanFactory(user=user)

        response = api_client.get(f"/api/v1/daily-plans/{plan.date.isoformat()}/")
        assert response.status_code == 200
        assert response.data["date"] == plan.date.isoformat()

    def test_add_item_to_daily_plan(self, api_client, user):
        plan = DailyPlanFactory(user=user)
        todo = PersonalTodoFactory(user=user)

        response = api_client.post(
            f"/api/v1/daily-plans/{plan.date.isoformat()}/add-item/",
            {"todo": todo.id},
        )
        assert response.status_code == 201
        assert len(response.data["items"]) == 1

    def test_remove_item_from_daily_plan(self, api_client, user):
        from apps.todos.models import DailyPlanItem

        plan = DailyPlanFactory(user=user)
        todo = PersonalTodoFactory(user=user)
        item = DailyPlanItem.objects.create(daily_plan=plan, todo=todo, order=0)

        response = api_client.post(
            f"/api/v1/daily-plans/{plan.date.isoformat()}/remove-item/",
            {"item_id": item.id},
        )
        assert response.status_code == 200
        assert len(response.data["items"]) == 0

    def test_reorder_daily_plan(self, api_client, user):
        from apps.todos.models import DailyPlanItem

        plan = DailyPlanFactory(user=user)
        todo1 = PersonalTodoFactory(user=user)
        todo2 = PersonalTodoFactory(user=user)
        item1 = DailyPlanItem.objects.create(daily_plan=plan, todo=todo1, order=0)
        item2 = DailyPlanItem.objects.create(daily_plan=plan, todo=todo2, order=1)

        response = api_client.post(
            f"/api/v1/daily-plans/{plan.date.isoformat()}/reorder/",
            {"items": [{"id": item1.id, "order": 1}, {"id": item2.id, "order": 0}]},
            format="json",
        )
        assert response.status_code == 200

    def test_remove_item_missing_id(self, api_client, user):
        plan = DailyPlanFactory(user=user)

        response = api_client.post(
            f"/api/v1/daily-plans/{plan.date.isoformat()}/remove-item/",
            {},
        )
        assert response.status_code == 400
