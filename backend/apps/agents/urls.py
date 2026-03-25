from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AgentProfileViewSet,
    AgentTaskViewSet,
    company_status,
    task_stream,
    webhook_event,
)

router = DefaultRouter()
router.register(r"tasks", AgentTaskViewSet, basename="agent-task")
router.register(r"profiles", AgentProfileViewSet, basename="agent-profile")

urlpatterns = [
    path("", include(router.urls)),
    path("webhooks/event/", webhook_event, name="agent-webhook"),
    path("tasks/<int:task_id>/stream/", task_stream, name="agent-task-stream"),
    path("company/status/", company_status, name="agent-company-status"),
]
