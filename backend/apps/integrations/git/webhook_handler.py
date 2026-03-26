"""GitHub Webhook Handler — empfaengt und verarbeitet GitHub Webhook Events."""

import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.integrations.models import GitActivity, IntegrationConfig
from apps.projects.models import Comment, Issue, Project

from .mappers import github_issue_to_local

logger = logging.getLogger(__name__)


def _verify_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Verifiziere GitHub Webhook HMAC-SHA256 Signatur."""
    if not signature or not secret:
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _find_integration_for_repo(repo_full_name: str) -> IntegrationConfig | None:
    """Finde die passende IntegrationConfig fuer ein Repository."""
    integrations = IntegrationConfig.objects.filter(
        integration_type=IntegrationConfig.IntegrationType.GITHUB,
        is_enabled=True,
    )
    for integration in integrations:
        repos = integration.settings.get("repos", [])
        for repo_config in repos:
            full = f"{repo_config.get('owner', '')}/{repo_config.get('repo', '')}"
            if full == repo_full_name:
                return integration
    return None


def _find_project_for_repo(integration: IntegrationConfig, repo_full_name: str) -> Project | None:
    """Finde das Projekt fuer ein Repository aus der Integration-Config."""
    repos = integration.settings.get("repos", [])
    for repo_config in repos:
        full = f"{repo_config.get('owner', '')}/{repo_config.get('repo', '')}"
        if full == repo_full_name:
            project_id = repo_config.get("project_id")
            if project_id:
                try:
                    return Project.objects.get(id=project_id)
                except Project.DoesNotExist:
                    pass
    return None


@csrf_exempt
@require_POST
def github_webhook(request):
    """Empfange und verarbeite GitHub Webhook Events."""
    event_type = request.headers.get("X-GitHub-Event", "")
    signature = request.headers.get("X-Hub-Signature-256", "")

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Repository identifizieren
    repo_data = payload.get("repository", {})
    repo_full_name = repo_data.get("full_name", "")
    if not repo_full_name:
        return JsonResponse({"error": "No repository"}, status=400)

    # Integration finden
    integration = _find_integration_for_repo(repo_full_name)
    if not integration:
        return JsonResponse({"error": "Unknown repository"}, status=404)

    # Signatur pruefen
    webhook_secret = integration.settings.get("webhook_secret", "")
    if webhook_secret and not _verify_signature(request.body, signature, webhook_secret):
        return JsonResponse({"error": "Invalid signature"}, status=403)

    project = _find_project_for_repo(integration, repo_full_name)
    if not project:
        return JsonResponse({"error": "No project mapped"}, status=404)

    # Event-Handler dispatchen
    handler = EVENT_HANDLERS.get(event_type)
    if handler:
        try:
            handler(payload, project, repo_full_name)
        except Exception:
            logger.exception("Fehler beim Verarbeiten von Webhook-Event %s", event_type)
            return JsonResponse({"error": "Processing failed"}, status=500)

    return JsonResponse({"status": "ok", "event": event_type})


def handle_issues_event(payload: dict, project: Project, repo_full_name: str):
    """Verarbeite issues / issues.opened / issues.edited / issues.closed Events."""
    action = payload.get("action", "")
    gh_issue = payload.get("issue", {})
    github_id = gh_issue.get("id")

    if not github_id:
        return

    if action in ("opened", "edited", "closed", "reopened"):
        local_data = github_issue_to_local(gh_issue, project, repo_full_name)
        github_issue_id = local_data.pop("github_issue_id")

        # Assignee mitsynchronisieren
        assignee = gh_issue.get("assignee")
        if assignee:
            local_data["github_assignee_login"] = assignee.get("login", "")
        else:
            local_data["github_assignee_login"] = ""

        Issue.objects.update_or_create(
            github_issue_id=github_issue_id,
            defaults=local_data,
        )
        logger.info("Issue %s via Webhook aktualisiert: %s", github_id, action)

    if action == "assigned" or action == "unassigned":
        try:
            issue = Issue.objects.get(github_issue_id=github_id)
            assignee = gh_issue.get("assignee")
            issue.github_assignee_login = assignee.get("login", "") if assignee else ""
            issue.save(update_fields=["github_assignee_login", "updated_at"])
        except Issue.DoesNotExist:
            pass


def handle_issue_comment_event(payload: dict, project: Project, repo_full_name: str):
    """Verarbeite issue_comment Events (created, edited, deleted)."""
    action = payload.get("action", "")
    comment_data = payload.get("comment", {})
    gh_issue = payload.get("issue", {})
    comment_id = comment_data.get("id")

    if not comment_id:
        return

    # Issue finden
    github_issue_id = gh_issue.get("id")
    try:
        issue = Issue.objects.get(github_issue_id=github_issue_id)
    except Issue.DoesNotExist:
        return

    if action in ("created", "edited"):
        # Wir brauchen einen Default-Autor
        from django.contrib.auth import get_user_model
        User = get_user_model()
        default_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not default_user:
            return

        Comment.objects.update_or_create(
            github_comment_id=comment_id,
            defaults={
                "issue": issue,
                "author": default_user,
                "body": comment_data.get("body", ""),
            },
        )
        logger.info("Kommentar %s via Webhook aktualisiert: %s", comment_id, action)

    elif action == "deleted":
        Comment.objects.filter(github_comment_id=comment_id).delete()
        logger.info("Kommentar %s via Webhook geloescht", comment_id)


def handle_push_event(payload: dict, project: Project, repo_full_name: str):
    """Verarbeite push Events — neue Commits registrieren."""
    from .sync import GitHubSyncService

    commits = payload.get("commits", [])
    for commit_data in commits:
        sha = commit_data.get("id", "")
        if not sha:
            continue

        sync_service_cls = GitHubSyncService  # fuer _link_to_issue
        message = commit_data.get("message", "")

        GitActivity.objects.update_or_create(
            external_id=sha,
            defaults={
                "project": project,
                "event_type": GitActivity.EventType.COMMIT,
                "author": commit_data.get("author", {}).get("name", ""),
                "title": message[:500],
                "url": commit_data.get("url", ""),
                "event_date": commit_data.get("timestamp", timezone.now()),
            },
        )


def handle_pull_request_event(payload: dict, project: Project, repo_full_name: str):
    """Verarbeite pull_request Events."""
    action = payload.get("action", "")
    pr_data = payload.get("pull_request", {})
    pr_id = str(pr_data.get("id", ""))

    if not pr_id:
        return

    merged = pr_data.get("merged_at") is not None
    state = pr_data.get("state", "")

    if merged:
        event_type = GitActivity.EventType.PR_MERGED
    elif state == "closed":
        event_type = GitActivity.EventType.PR_CLOSED
    else:
        event_type = GitActivity.EventType.PR_OPENED

    GitActivity.objects.update_or_create(
        external_id=f"pr-{pr_id}",
        defaults={
            "project": project,
            "event_type": event_type,
            "author": pr_data.get("user", {}).get("login", ""),
            "title": pr_data.get("title", "")[:500],
            "url": pr_data.get("html_url", ""),
            "event_date": pr_data.get("updated_at", timezone.now()),
        },
    )


def handle_pull_request_review_event(payload: dict, project: Project, repo_full_name: str):
    """Verarbeite pull_request_review Events (#23)."""
    review = payload.get("review", {})
    pr_data = payload.get("pull_request", {})

    review_id = review.get("id")
    if not review_id:
        return

    GitActivity.objects.update_or_create(
        external_id=f"review-{review_id}",
        defaults={
            "project": project,
            "event_type": GitActivity.EventType.PR_REVIEWED,
            "author": review.get("user", {}).get("login", ""),
            "title": f"Review on: {pr_data.get('title', '')[:400]}",
            "description": review.get("body", "") or "",
            "url": review.get("html_url", ""),
            "event_date": review.get("submitted_at", timezone.now()),
        },
    )


# Event-Handler Dispatch-Table
EVENT_HANDLERS = {
    "issues": handle_issues_event,
    "issue_comment": handle_issue_comment_event,
    "push": handle_push_event,
    "pull_request": handle_pull_request_event,
    "pull_request_review": handle_pull_request_review_event,
}

# Events die bei der Webhook-Registrierung abonniert werden
WEBHOOK_EVENTS = [
    "issues",
    "issue_comment",
    "push",
    "pull_request",
    "pull_request_review",
]
