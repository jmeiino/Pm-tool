from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .import_views import ConfluenceImportViewSet, GitHubImportViewSet, ImportDashboardViewSet, JiraImportViewSet
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
router.register(r"import/jira", JiraImportViewSet, basename="import-jira")
router.register(r"import/github", GitHubImportViewSet, basename="import-github")
router.register(r"import/confluence", ConfluenceImportViewSet, basename="import-confluence")
router.register(r"import/dashboard", ImportDashboardViewSet, basename="import-dashboard")

urlpatterns = [
    path("", include(router.urls)),
    path("microsoft/auth/", microsoft_auth_start, name="microsoft-auth-start"),
    path("microsoft/callback/", microsoft_auth_callback, name="microsoft-auth-callback"),
]
