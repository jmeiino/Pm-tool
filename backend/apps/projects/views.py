from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Comment, Issue, Label, Project, Sprint
from .serializers import (
    CommentSerializer,
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
        return Response({
            "total": issues.count(),
            "by_status": dict(
                issues.values_list("status").annotate(count=Count("id")).values_list("status", "count")
            ),
            "by_type": dict(
                issues.values_list("issue_type").annotate(count=Count("id")).values_list("issue_type", "count")
            ),
        })


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
        return IssueListSerializer

    def get_queryset(self):
        return Issue.objects.select_related("project", "assignee", "sprint").prefetch_related(
            "labels", "comments", "subtasks"
        )


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
