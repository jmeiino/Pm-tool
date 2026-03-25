import logging
import re

from django.utils import timezone

from apps.integrations.models import GitActivity, IntegrationConfig, SyncLog
from apps.projects.models import Issue, Project

from .client import GitHubClient
from .mappers import github_issue_to_local

logger = logging.getLogger(__name__)


class GitHubSyncService:
    """Service für die Synchronisierung mit GitHub."""

    def __init__(self, integration: IntegrationConfig):
        self.integration = integration
        creds = integration.credentials
        self.client = GitHubClient(token=creds.get("token", creds.get("access_token", "")))

    def sync_commits(self, project: Project, owner: str, repo: str) -> int:
        """Commits synchronisieren."""
        since = None
        if self.integration.last_synced_at:
            since = self.integration.last_synced_at.isoformat()

        commits = self.client.get_commits(owner, repo, since=since)
        created = 0

        for commit_data in commits:
            sha = commit_data.get("sha", "")
            if not sha:
                continue

            _, was_created = GitActivity.objects.update_or_create(
                external_id=sha,
                defaults={
                    "project": project,
                    "event_type": GitActivity.EventType.COMMIT,
                    "author": commit_data.get("commit", {}).get("author", {}).get("name", ""),
                    "title": commit_data.get("commit", {}).get("message", "")[:500],
                    "url": commit_data.get("html_url", ""),
                    "event_date": commit_data.get("commit", {}).get("author", {}).get("date", timezone.now()),
                    "linked_issue": self._link_to_issue(commit_data.get("commit", {}).get("message", ""), project),
                },
            )
            if was_created:
                created += 1

        return created

    def sync_pull_requests(self, project: Project, owner: str, repo: str) -> int:
        """Pull Requests synchronisieren."""
        prs = self.client.get_pull_requests(owner, repo, state="all")
        created = 0

        for pr_data in prs:
            pr_id = str(pr_data.get("id", ""))
            state = pr_data.get("state", "")
            merged = pr_data.get("merged_at") is not None

            if merged:
                event_type = GitActivity.EventType.PR_MERGED
            elif state == "closed":
                event_type = GitActivity.EventType.PR_CLOSED
            else:
                event_type = GitActivity.EventType.PR_OPENED

            _, was_created = GitActivity.objects.update_or_create(
                external_id=f"pr-{pr_id}",
                defaults={
                    "project": project,
                    "event_type": event_type,
                    "author": pr_data.get("user", {}).get("login", ""),
                    "title": pr_data.get("title", "")[:500],
                    "url": pr_data.get("html_url", ""),
                    "event_date": pr_data.get("updated_at", timezone.now()),
                    "linked_issue": self._link_to_issue(pr_data.get("title", ""), project),
                },
            )
            if was_created:
                created += 1

        return created

    def sync_issues(self, project: Project, owner: str, repo: str) -> tuple[int, int]:
        """GitHub Issues synchronisieren (nur für Projekte mit importierten Issues)."""
        full_name = f"{owner}/{repo}"

        # Nur synchronisieren wenn es bereits importierte GitHub Issues gibt
        has_github_issues = Issue.objects.filter(
            project=project, github_repo_full_name=full_name
        ).exists()
        if not has_github_issues:
            return 0, 0

        gh_issues = self.client.get_issues(owner, repo, state="all")
        created = 0
        updated = 0

        for gh_issue in gh_issues:
            github_id = gh_issue.get("id")
            if not github_id:
                continue

            # Nur Issues aktualisieren die bereits importiert wurden
            existing = Issue.objects.filter(github_issue_id=github_id).first()
            if not existing:
                continue

            local_data = github_issue_to_local(gh_issue, project, full_name)
            github_issue_id = local_data.pop("github_issue_id")
            _, was_created = Issue.objects.update_or_create(
                github_issue_id=github_issue_id,
                defaults=local_data,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return created, updated

    def sync_inbound(self) -> SyncLog:
        """Eingehender Sync: GitHub -> lokal."""
        sync_log = SyncLog.objects.create(
            integration=self.integration,
            direction=SyncLog.Direction.INBOUND,
            status=SyncLog.Status.STARTED,
            started_at=timezone.now(),
        )

        total_created = 0
        total_updated = 0
        errors = []

        try:
            repos = self.integration.settings.get("repos", [])
            for repo_config in repos:
                owner = repo_config.get("owner", "")
                repo = repo_config.get("repo", "")
                project_id = repo_config.get("project_id")

                if not (owner and repo and project_id):
                    continue

                try:
                    project = Project.objects.get(id=project_id)
                    total_created += self.sync_commits(project, owner, repo)
                    total_created += self.sync_pull_requests(project, owner, repo)
                    issues_created, issues_updated = self.sync_issues(project, owner, repo)
                    total_created += issues_created
                    total_updated += issues_updated
                except Project.DoesNotExist:
                    errors.append(f"Projekt {project_id} nicht gefunden")
                except Exception as e:
                    errors.append(f"Fehler bei {owner}/{repo}: {str(e)}")

            sync_log.status = SyncLog.Status.COMPLETED
        except Exception as e:
            sync_log.status = SyncLog.Status.FAILED
            errors.append(str(e))

        sync_log.records_processed = total_created + total_updated
        sync_log.records_created = total_created
        sync_log.records_updated = total_updated
        sync_log.errors = errors
        sync_log.completed_at = timezone.now()
        sync_log.save()

        return sync_log

    def _link_to_issue(self, text: str, project: Project) -> Issue | None:
        """Parse issue keys from text (e.g. PRJ-123)."""
        pattern = rf"\b{re.escape(project.key)}-(\d+)\b"
        match = re.search(pattern, text)
        if match:
            try:
                return Issue.objects.get(key=match.group(0), project=project)
            except Issue.DoesNotExist:
                pass
        return None
