import logging
import re

from django.utils import timezone

from apps.integrations.models import GitActivity, IntegrationConfig, SyncLog
from apps.projects.models import Comment, Issue, Project, Sprint

from .client import GitHubClient
from .mappers import (
    github_issue_to_local,
    github_milestone_to_sprint,
    local_issue_to_github,
)

logger = logging.getLogger(__name__)


class GitHubSyncService:
    """Service fuer die Synchronisierung mit GitHub."""

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

    def sync_issues(self, project: Project, owner: str, repo: str, auto_import: bool = True) -> tuple[int, int]:
        """GitHub Issues synchronisieren.

        #17: Mit auto_import=True werden auch neue Issues automatisch importiert,
        nicht nur bereits bekannte.
        """
        full_name = f"{owner}/{repo}"

        # Pruefen ob Auto-Import aktiv ist (Standard: True)
        repo_settings = self._get_repo_settings(owner, repo)
        auto_import = repo_settings.get("auto_import_issues", auto_import)

        gh_issues = self.client.get_issues(owner, repo, state="all")
        created = 0
        updated = 0

        for gh_issue in gh_issues:
            github_id = gh_issue.get("id")
            if not github_id:
                continue

            existing = Issue.objects.filter(github_issue_id=github_id).first()

            if existing:
                # Update bestehendes Issue
                local_data = github_issue_to_local(gh_issue, project, full_name)
                local_data.pop("github_issue_id")
                for field, value in local_data.items():
                    setattr(existing, field, value)
                existing.save()
                updated += 1
            elif auto_import:
                # #17: Neues Issue automatisch importieren
                local_data = github_issue_to_local(gh_issue, project, full_name)
                Issue.objects.create(**local_data)
                created += 1

        return created, updated

    def sync_comments(self, project: Project, owner: str, repo: str) -> tuple[int, int]:
        """Issue-Kommentare synchronisieren (#19).

        Fuer jedes lokal bekannte Issue werden die GitHub-Kommentare geholt.
        """
        full_name = f"{owner}/{repo}"
        created = 0
        updated = 0

        issues_with_github = Issue.objects.filter(
            project=project,
            github_issue_number__isnull=False,
            github_repo_full_name=full_name,
        )

        from django.contrib.auth import get_user_model
        User = get_user_model()
        default_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not default_user:
            logger.warning("Kein Default-User fuer Kommentar-Import vorhanden")
            return 0, 0

        for issue in issues_with_github:
            try:
                gh_comments = self.client.get_issue_comments(owner, repo, issue.github_issue_number)
            except Exception:
                logger.warning("Fehler beim Laden der Kommentare fuer %s", issue.key)
                continue

            for gh_comment in gh_comments:
                comment_id = gh_comment.get("id")
                if not comment_id:
                    continue

                _, was_created = Comment.objects.update_or_create(
                    github_comment_id=comment_id,
                    defaults={
                        "issue": issue,
                        "author": default_user,
                        "body": gh_comment.get("body", ""),
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        return created, updated

    def sync_comments_outbound(self, project: Project, owner: str, repo: str) -> tuple[int, int]:
        """Lokale Kommentare nach GitHub pushen (#19)."""
        full_name = f"{owner}/{repo}"
        created = 0
        updated = 0

        issues_with_github = Issue.objects.filter(
            project=project,
            github_issue_number__isnull=False,
            github_repo_full_name=full_name,
        )

        for issue in issues_with_github:
            # Neue Kommentare (ohne github_comment_id)
            new_comments = Comment.objects.filter(
                issue=issue,
                github_comment_id__isnull=True,
            )
            for comment in new_comments:
                try:
                    result = self.client.create_issue_comment(
                        owner, repo, issue.github_issue_number, comment.body
                    )
                    comment.github_comment_id = result.get("id")
                    comment.save(update_fields=["github_comment_id", "updated_at"])
                    created += 1
                except Exception:
                    logger.warning("Fehler beim Pushen von Kommentar %s", comment.id)

            # Geaenderte Kommentare
            if self.integration.last_synced_at:
                changed_comments = Comment.objects.filter(
                    issue=issue,
                    github_comment_id__isnull=False,
                    updated_at__gt=self.integration.last_synced_at,
                )
                for comment in changed_comments:
                    try:
                        self.client.update_issue_comment(
                            owner, repo, comment.github_comment_id, comment.body
                        )
                        updated += 1
                    except Exception:
                        logger.warning("Fehler beim Update von Kommentar %s", comment.github_comment_id)

        return created, updated

    def sync_milestones(self, project: Project, owner: str, repo: str) -> tuple[int, int]:
        """GitHub Milestones mit Sprints synchronisieren (#21)."""
        milestones = self.client.get_milestones(owner, repo, state="all")
        created = 0
        updated = 0

        for milestone in milestones:
            milestone_id = milestone.get("id")
            if not milestone_id:
                continue

            sprint_data = github_milestone_to_sprint(milestone, project)
            github_milestone_id = sprint_data.pop("github_milestone_id")

            _, was_created = Sprint.objects.update_or_create(
                github_milestone_id=github_milestone_id,
                defaults=sprint_data,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        # Issues ihren Sprints zuordnen basierend auf Milestone
        self._assign_issues_to_sprints(project, owner, repo)

        return created, updated

    def _assign_issues_to_sprints(self, project: Project, owner: str, repo: str):
        """Weise Issues basierend auf GitHub Milestone dem richtigen Sprint zu."""
        full_name = f"{owner}/{repo}"
        issues = Issue.objects.filter(
            project=project,
            github_issue_number__isnull=False,
            github_repo_full_name=full_name,
        )

        # Lade Issues von GitHub um Milestone-Zuordnung zu sehen
        try:
            gh_issues = self.client.get_issues(owner, repo, state="all")
        except Exception:
            return

        gh_issues_by_id = {i["id"]: i for i in gh_issues}

        for issue in issues:
            gh_issue = gh_issues_by_id.get(issue.github_issue_id)
            if not gh_issue:
                continue

            milestone = gh_issue.get("milestone")
            if milestone:
                milestone_id = milestone.get("id")
                try:
                    sprint = Sprint.objects.get(github_milestone_id=milestone_id)
                    if issue.sprint_id != sprint.id:
                        issue.sprint = sprint
                        issue.save(update_fields=["sprint", "updated_at"])
                except Sprint.DoesNotExist:
                    pass
            elif issue.sprint and issue.sprint.github_milestone_id:
                # Milestone wurde entfernt
                issue.sprint = None
                issue.save(update_fields=["sprint", "updated_at"])

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

                    # Kommentare synchronisieren (#19)
                    comments_created, comments_updated = self.sync_comments(project, owner, repo)
                    total_created += comments_created
                    total_updated += comments_updated

                    # Milestones synchronisieren (#21)
                    milestones_created, milestones_updated = self.sync_milestones(project, owner, repo)
                    total_created += milestones_created
                    total_updated += milestones_updated

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

    def detect_conflicts(self, project: Project, owner: str, repo: str) -> list[dict]:
        """Konflikte erkennen: lokal UND remote geaenderte Issues seit letztem Sync."""
        if not self.integration.last_synced_at:
            return []

        full_name = f"{owner}/{repo}"
        last_sync = self.integration.last_synced_at

        # Lokal geaenderte Issues
        locally_changed = Issue.objects.filter(
            project=project,
            github_issue_id__isnull=False,
            github_issue_number__isnull=False,
            github_repo_full_name=full_name,
            updated_at__gt=last_sync,
        )

        if not locally_changed.exists():
            return []

        # Remote Issues holen
        try:
            gh_issues = self.client.get_issues(owner, repo, state="all")
        except Exception:
            logger.warning("Fehler beim Laden der Issues fuer Konflikterkennung: %s/%s", owner, repo)
            return []

        gh_issues_by_id = {i["id"]: i for i in gh_issues}
        conflicts = []

        for issue in locally_changed:
            gh_issue = gh_issues_by_id.get(issue.github_issue_id)
            if not gh_issue:
                continue

            # Remote updated_at pruefen
            gh_updated = gh_issue.get("updated_at", "")
            if not gh_updated:
                continue

            from django.utils.dateparse import parse_datetime
            gh_updated_dt = parse_datetime(gh_updated)
            if gh_updated_dt and gh_updated_dt > last_sync:
                # Beide Seiten haben sich geaendert -> Konflikt
                local_title = issue.title
                remote_title = gh_issue.get("title", "")
                local_status = issue.status
                remote_state = gh_issue.get("state", "")

                conflicts.append({
                    "issue_key": issue.key,
                    "github_issue_number": issue.github_issue_number,
                    "local_title": local_title,
                    "remote_title": remote_title,
                    "local_status": local_status,
                    "remote_state": remote_state,
                    "local_updated": issue.updated_at.isoformat(),
                    "remote_updated": gh_updated,
                    "has_title_conflict": local_title != remote_title,
                    "has_status_conflict": (
                        local_status in ("done",) and remote_state == "open"
                    ) or (
                        local_status in ("to_do", "in_progress") and remote_state == "closed"
                    ),
                })

        return conflicts

    def sync_outbound(self) -> SyncLog:
        """Ausgehender Sync: lokal geaenderte GitHub Issues -> GitHub."""
        sync_log = SyncLog.objects.create(
            integration=self.integration,
            direction=SyncLog.Direction.OUTBOUND,
            status=SyncLog.Status.STARTED,
            started_at=timezone.now(),
        )

        total_updated = 0
        total_created = 0
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
                except Project.DoesNotExist:
                    errors.append(f"Projekt {project_id} nicht gefunden")
                    continue

                full_name = f"{owner}/{repo}"

                # Bestehende GitHub Issues aktualisieren
                if self.integration.last_synced_at:
                    changed_issues = Issue.objects.filter(
                        project=project,
                        github_issue_id__isnull=False,
                        github_issue_number__isnull=False,
                        github_repo_full_name=full_name,
                        updated_at__gt=self.integration.last_synced_at,
                    )
                    for issue in changed_issues:
                        try:
                            payload = local_issue_to_github(issue)
                            self.client.update_issue(owner, repo, issue.github_issue_number, payload)
                            total_updated += 1
                        except Exception as e:
                            errors.append(f"Fehler beim Update von {issue.key}: {str(e)}")

                # Neue lokale Issues nach GitHub pushen
                new_issues = Issue.objects.filter(
                    project=project,
                    github_issue_id__isnull=True,
                    github_repo_full_name=full_name,
                )
                for issue in new_issues:
                    try:
                        payload = local_issue_to_github(issue)
                        result = self.client.create_issue(
                            owner, repo,
                            title=payload["title"],
                            body=payload.get("body", ""),
                            labels=payload.get("labels"),
                        )
                        issue.github_issue_id = result.get("id")
                        issue.github_issue_number = result.get("number")
                        issue.save(update_fields=[
                            "github_issue_id", "github_issue_number", "updated_at"
                        ])
                        total_created += 1
                    except Exception as e:
                        errors.append(f"Fehler beim Erstellen von {issue.key}: {str(e)}")

                # Kommentare synchronisieren (#19)
                try:
                    comments_created, comments_updated = self.sync_comments_outbound(project, owner, repo)
                    total_created += comments_created
                    total_updated += comments_updated
                except Exception as e:
                    errors.append(f"Fehler bei Kommentar-Sync {owner}/{repo}: {str(e)}")

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

    def register_webhook(self, owner: str, repo: str, callback_url: str) -> dict | None:
        """Webhook fuer ein Repository registrieren (#16).

        Prueft ob bereits ein Webhook existiert und erstellt ggf. einen neuen.
        Speichert das Webhook-Secret in den Integration-Settings.
        """
        from .webhook_handler import WEBHOOK_EVENTS

        # Pruefen ob bereits ein Webhook aktiv ist
        try:
            existing_hooks = self.client.get_webhooks(owner, repo)
            for hook in existing_hooks:
                config = hook.get("config", {})
                if config.get("url") == callback_url:
                    logger.info("Webhook fuer %s/%s bereits registriert", owner, repo)
                    return hook
        except Exception:
            logger.warning("Konnte bestehende Webhooks fuer %s/%s nicht pruefen", owner, repo)

        # Neuen Webhook erstellen
        try:
            result = self.client.create_webhook(owner, repo, callback_url, WEBHOOK_EVENTS)
            webhook_secret = result.pop("secret", "")

            # Secret in Integration-Settings speichern
            settings = self.integration.settings
            settings["webhook_secret"] = webhook_secret
            self.integration.settings = settings
            self.integration.save(update_fields=["settings", "updated_at"])

            logger.info("Webhook fuer %s/%s registriert (ID: %s)", owner, repo, result.get("id"))
            return result
        except Exception:
            logger.exception("Fehler beim Registrieren des Webhooks fuer %s/%s", owner, repo)
            return None

    def _get_repo_settings(self, owner: str, repo: str) -> dict:
        """Hole repo-spezifische Settings aus der Integration-Konfiguration."""
        repos = self.integration.settings.get("repos", [])
        for repo_config in repos:
            if repo_config.get("owner") == owner and repo_config.get("repo") == repo:
                return repo_config
        return {}

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
