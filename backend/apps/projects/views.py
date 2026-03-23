from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Comment, Issue, Label, Project, Sprint
from .serializers import (
    CommentSerializer,
    IssueCreateSerializer,
    IssueDetailSerializer,
    IssueListSerializer,
    LabelSerializer,
    ProjectSerializer,
    SprintSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    filterset_fields = ["status", "is_synced"]
    search_fields = ["name", "key"]
    ordering_fields = ["name", "created_at", "updated_at"]

    def get_queryset(self):
        return Project.objects.annotate(issue_count=Count("issues"))

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        project = self.get_object()
        issues = project.issues.all()
        today = timezone.now().date()
        active_sprint = project.sprints.filter(status=Sprint.Status.ACTIVE).first()

        stats = {
            "total": issues.count(),
            "by_status": dict(
                issues.values_list("status").annotate(count=Count("id")).values_list("status", "count")
            ),
            "by_type": dict(
                issues.values_list("issue_type").annotate(count=Count("id")).values_list("issue_type", "count")
            ),
            "by_priority": dict(
                issues.values_list("priority").annotate(count=Count("id")).values_list("priority", "count")
            ),
            "overdue_count": issues.filter(due_date__lt=today, status__in=["to_do", "in_progress"]).count(),
        }

        if active_sprint:
            sprint_issues = issues.filter(sprint=active_sprint)
            stats["sprint_info"] = {
                "name": active_sprint.name,
                "start_date": active_sprint.start_date,
                "end_date": active_sprint.end_date,
                "total_issues": sprint_issues.count(),
                "done_issues": sprint_issues.filter(status="done").count(),
            }

        return Response(stats)


class SprintViewSet(viewsets.ModelViewSet):
    serializer_class = SprintSerializer
    filterset_fields = ["project", "status"]
    ordering_fields = ["start_date", "end_date"]

    def get_queryset(self):
        qs = Sprint.objects.select_related("project")
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs


class IssueViewSet(viewsets.ModelViewSet):
    filterset_fields = ["project", "sprint", "status", "issue_type", "priority", "assignee"]
    search_fields = ["title", "key", "description"]
    ordering_fields = ["created_at", "updated_at", "priority", "due_date"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return IssueDetailSerializer
        if self.action in ("create", "update", "partial_update"):
            return IssueCreateSerializer
        return IssueListSerializer

    def get_queryset(self):
        return Issue.objects.select_related("project", "assignee", "sprint", "reporter").prefetch_related(
            "labels", "comments", "subtasks"
        )

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        """Status eines Issues ändern."""
        issue = self.get_object()
        new_status = request.data.get("status")
        if not new_status:
            return Response({"detail": "Status ist erforderlich."}, status=400)
        issue.status = new_status
        issue.save(update_fields=["status", "updated_at"])
        return Response(IssueDetailSerializer(issue).data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        return Comment.objects.select_related("author", "issue").filter(
            issue_id=self.kwargs.get("issue_pk")
        )

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            issue_id=self.kwargs.get("issue_pk"),
        )


class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    search_fields = ["name"]
