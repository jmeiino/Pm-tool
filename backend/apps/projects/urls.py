from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, IssueViewSet, LabelViewSet, ProjectViewSet, SprintViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"sprints", SprintViewSet, basename="sprint")
router.register(r"issues", IssueViewSet, basename="issue")
router.register(r"labels", LabelViewSet, basename="label")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "issues/<int:issue_pk>/comments/",
        CommentViewSet.as_view({"get": "list", "post": "create"}),
        name="issue-comments",
    ),
]
