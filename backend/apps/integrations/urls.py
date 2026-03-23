from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .microsoft.views import microsoft_auth_callback, microsoft_auth_start
from .views import (
    CalendarEventViewSet,
    ConfluencePageViewSet,
    GitActivityViewSet,
    GitRepoAnalysisViewSet,
    IntegrationConfigViewSet,
    SyncLogViewSet,
)

router = DefaultRouter()
router.register(r"configs", IntegrationConfigViewSet, basename="integration-config")
router.register(r"sync-logs", SyncLogViewSet, basename="sync-log")
router.register(r"confluence-pages", ConfluencePageViewSet, basename="confluence-page")
router.register(r"calendar-events", CalendarEventViewSet, basename="calendar-event")
router.register(r"git-activities", GitActivityViewSet, basename="git-activity")
router.register(r"repo-analyses", GitRepoAnalysisViewSet, basename="repo-analysis")

urlpatterns = [
    path("", include(router.urls)),
    path("microsoft/auth/", microsoft_auth_start, name="microsoft-auth-start"),
    path("microsoft/callback/", microsoft_auth_callback, name="microsoft-auth-callback"),
]
