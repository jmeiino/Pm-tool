import json
import logging

from django.utils import timezone

from config.celery import app

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_github_updates(self, integration_id: int):
    """Periodischer Task: Neue Änderungen aus GitHub abrufen."""
    from apps.integrations.models import IntegrationConfig
    from apps.notifications.services import NotificationService

    try:
        integration = IntegrationConfig.objects.get(id=integration_id)
    except IntegrationConfig.DoesNotExist:
        logger.error("Integration %s nicht gefunden", integration_id)
        return

    try:
        from .sync import GitHubSyncService

        sync_service = GitHubSyncService(integration)
        sync_service.sync_inbound()

        integration.last_synced_at = timezone.now()
        integration.sync_status = IntegrationConfig.SyncStatus.IDLE
        integration.save(update_fields=["last_synced_at", "sync_status", "updated_at"])
    except Exception as exc:
        integration.sync_status = IntegrationConfig.SyncStatus.ERROR
        integration.save(update_fields=["sync_status", "updated_at"])

        NotificationService.create_notification(
            user=integration.user,
            title="GitHub-Sync fehlgeschlagen",
            message=str(exc),
            notification_type="sync_error",
            severity="warning",
        )
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_github_repo_task(self, repo_analysis_id: int):
    """Repository-Daten von GitHub abrufen und per KI analysieren."""
    from apps.ai.services import AIService
    from apps.integrations.models import GitRepoAnalysis, IntegrationConfig

    try:
        repo = GitRepoAnalysis.objects.get(id=repo_analysis_id)
    except GitRepoAnalysis.DoesNotExist:
        logger.error("GitRepoAnalysis %s nicht gefunden", repo_analysis_id)
        return

    try:
        # GitHub-Client mit erstem aktiven GitHub-Token erstellen
        integration = IntegrationConfig.objects.filter(
            integration_type=IntegrationConfig.IntegrationType.GITHUB,
            is_enabled=True,
        ).first()

        if not integration:
            logger.error("Keine aktive GitHub-Integration gefunden")
            return

        from .client import GitHubClient

        token = integration.credentials.get("token", "")
        owner, repo_name = repo.repo_full_name.split("/", 1)

        with GitHubClient(token=token) as client:
            # Repository-Metadaten abrufen
            repo_info = client.get_repo(owner, repo_name)
            languages = client.get_languages(owner, repo_name)
            readme = client.get_readme(owner, repo_name)
            recent_commits = client.get_commits(owner, repo_name)[:20]

        # Modell mit GitHub-Daten aktualisieren
        repo.description = repo_info.get("description", "") or ""
        repo.primary_language = repo_info.get("language", "") or ""
        repo.languages = languages
        repo.stars = repo_info.get("stargazers_count", 0)
        repo.forks = repo_info.get("forks_count", 0)
        repo.open_issues_count = repo_info.get("open_issues_count", 0)
        repo.topics = repo_info.get("topics", [])
        repo.default_branch = repo_info.get("default_branch", "main")
        repo.readme_content = readme

        commits_text = "\n".join(
            f"- {c['commit']['message'].split(chr(10))[0]} ({c['commit']['author']['name']})"
            for c in recent_commits
            if c.get("commit")
        )
        repo.recent_commits_summary = commits_text

        # KI-Analyse durchfuehren
        repo_data = {
            "repo_name": repo.repo_full_name,
            "description": repo.description,
            "primary_language": repo.primary_language,
            "languages": json.dumps(languages),
            "stars": repo.stars,
            "forks": repo.forks,
            "open_issues": repo.open_issues_count,
            "topics": repo.topics,
            "readme": readme,
            "recent_commits": commits_text,
        }

        service = AIService()
        result = service.analyze_github_repo(repo_data)

        repo.ai_summary = result.get("summary", "")
        repo.ai_tech_stack = result.get("tech_stack", [])
        repo.ai_strengths = result.get("strengths", [])
        repo.ai_improvements = result.get("improvements", [])
        repo.ai_action_items = result.get("action_items", [])
        repo.ai_processed_at = timezone.now()
        repo.save()

        logger.info("Repository-Analyse abgeschlossen: %s", repo.repo_full_name)
    except Exception as exc:
        logger.error("Fehler bei Repository-Analyse %s: %s", repo_analysis_id, exc)
        raise self.retry(exc=exc)
