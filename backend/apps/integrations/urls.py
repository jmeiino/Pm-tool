from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CalendarEventViewSet,
    ConfluencePageViewSet,
    IntegrationConfigViewSet,
    SyncLogViewSet,
)

router = DefaultRouter()
router.register(r"configs", IntegrationConfigViewSet, basename="integration-config")
router.register(r"sync-logs", SyncLogViewSet, basename="sync-log")
router.register(r"confluence-pages", ConfluencePageViewSet, basename="confluence-page")
router.register(r"calendar-events", CalendarEventViewSet, basename="calendar-event")

urlpatterns = [
    path("", include(router.urls)),
]
