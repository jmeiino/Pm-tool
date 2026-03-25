"""Import-Wizard ViewSets: Preview (read-only) + Confirm (create records)."""

import logging
import re

from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integrations.models import ConfluencePage, IntegrationConfig
from apps.projects.models import Issue, Project

from .import_serializers import (
    ConfluenceConfirmRequestSerializer,
    ConfluencePreviewResponseSerializer,
    GitHubConfirmRequestSerializer,
    GitHubPreviewResponseSerializer,
    ImportConfirmResponseSerializer,
    JiraConfirmRequestSerializer,
    JiraPreviewResponseSerializer,
)

logger = logging.getLogger(__name__)


def _get_integration(user, integration_type: str) -> IntegrationConfig | None:
    """Hole die aktive IntegrationConfig für den User."""
    try:
        return IntegrationConfig.objects.get(
            user=user,
            integration_type=integration_type,
            is_enabled=True,
        )
    except IntegrationConfig.DoesNotExist:
        return None


PREVIEW_CACHE_TTL = 300  # 5 Minuten


def _cache_key(user_id: int, integration_type: str, extra: str = "") -> str:
    """Generiere einen Cache-Key für Preview-Daten."""
    return f"import_preview:{user_id}:{integration_type}:{extra}"


def _make_project_key(name: str) -> str:
    """Generiere einen Projekt-Key aus dem Namen."""
    key = re.sub(r"[^A-Za-z0-9]", "", name).upper()[:10]
    if not key:
        key = "PROJ"
    # Stelle sicher, dass der Key eindeutig ist
    base_key = key
    counter = 1
    while Project.objects.filter(key=key).exists():
        key = f"{base_key[:8]}{counter}"
        counter += 1
    return key


# ─── Jira Import ─────────────────────────────────────────────────────────────


class JiraImportViewSet(viewsets.ViewSet):
    """Jira-Daten voranzeigen und selektiv importieren."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def preview(self, request):
        """Jira-Projekte laden. Mit ?project_key=X Issues lazy nachladen."""
        integration = _get_integration(request.user, IntegrationConfig.IntegrationType.JIRA)
        if not integration:
            return Response(
                {"detail": "Keine aktive Jira-Integration gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.integrations.jira.client import JiraClient

        creds = integration.credentials
        client = JiraClient(url=creds["url"], email=creds["email"], api_token=creds["api_token"])

        project_key_param = request.query_params.get("project_key")

        if project_key_param:
            # Lazy Loading: Issues für ein einzelnes Projekt laden
            return self._preview_project_issues(client, project_key_param)

        # Standard: Nur Projekte laden (schnell), mit Cache
        ck = _cache_key(request.user.id, "jira", "projects")
        cached = cache.get(ck)
        if cached:
            return Response(cached)

        try:
            jira_projects = client.get_projects()
        except Exception:
            logger.exception("Fehler beim Laden der Jira-Projekte für Preview")
            return Response(
                {"detail": "Fehler beim Laden der Jira-Projekte."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        projects_data = []
        for jp in jira_projects:
            projects_data.append({
                "jira_id": jp.get("id", ""),
                "key": jp.get("key", ""),
                "name": jp.get("name", ""),
                "issues": [],
            })

        response_data = {
            "projects": projects_data,
            "available_assignees": [],
            "available_statuses": [],
            "available_sprints": [],
        }

        serializer = JiraPreviewResponseSerializer(response_data)
        cache.set(ck, serializer.data, PREVIEW_CACHE_TTL)
        return Response(serializer.data)

    def _preview_project_issues(self, client, project_key: str):
        """Issues eines einzelnen Jira-Projekts laden (Lazy Loading)."""
        try:
            issues_raw = client.get_issues(project_key)
        except Exception:
            logger.exception("Fehler beim Laden der Issues für %s", project_key)
            return Response(
                {"detail": f"Fehler beim Laden der Issues für {project_key}."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        all_assignees = set()
        all_statuses = set()
        all_sprints = set()
        issues_data = []

        for issue in issues_raw:
            fields = issue.get("fields", {})
            assignee_name = None
            if fields.get("assignee"):
                assignee_name = fields["assignee"].get("displayName") or fields["assignee"].get("emailAddress")
                if assignee_name:
                    all_assignees.add(assignee_name)

            status_name = None
            if fields.get("status"):
                status_name = fields["status"].get("name")
                if status_name:
                    all_statuses.add(status_name)

            sprint_name = None
            if fields.get("sprint"):
                sprint_name = fields["sprint"].get("name")
                if sprint_name:
                    all_sprints.add(sprint_name)

            issue_type_name = None
            if fields.get("issuetype"):
                issue_type_name = fields["issuetype"].get("name")

            issues_data.append({
                "jira_id": issue.get("id", ""),
                "key": issue.get("key", ""),
                "summary": fields.get("summary", ""),
                "status": status_name,
                "assignee": assignee_name,
                "sprint": sprint_name,
                "issue_type": issue_type_name,
                "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
            })

        response_data = {
            "projects": [{
                "jira_id": "",
                "key": project_key,
                "name": project_key,
                "issues": issues_data,
            }],
            "available_assignees": sorted(all_assignees),
            "available_statuses": sorted(all_statuses),
            "available_sprints": sorted(all_sprints),
        }

        serializer = JiraPreviewResponseSerializer(response_data)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def confirm(self, request):
        """Ausgewählte Jira-Projekte + Issues importieren."""
        serializer = JiraConfirmRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        integration = _get_integration(request.user, IntegrationConfig.IntegrationType.JIRA)
        if not integration:
            return Response(
                {"detail": "Keine aktive Jira-Integration gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.integrations.jira.client import JiraClient
        from apps.integrations.jira.mappers import jira_issue_to_local

        creds = integration.credentials
        client = JiraClient(url=creds["url"], email=creds["email"], api_token=creds["api_token"])

        created_count = 0
        updated_count = 0

        for proj_data in serializer.validated_data["projects"]:
            # Projekt erstellen oder aktualisieren
            project, proj_created = Project.objects.update_or_create(
                jira_project_id=proj_data["jira_project_id"],
                defaults={
                    "name": proj_data["name"],
                    "key": proj_data["jira_project_key"],
                    "jira_project_key": proj_data["jira_project_key"],
                    "is_synced": True,
                    "source": Project.Source.JIRA,
                    "owner": request.user,
                },
            )
            if proj_created:
                created_count += 1
            else:
                updated_count += 1

            # Issues importieren, falls IDs angegeben
            if proj_data.get("issue_ids"):
                selected_ids = set(proj_data["issue_ids"])
                try:
                    all_issues = client.get_issues(proj_data["jira_project_key"])
                except Exception:
                    logger.warning("Fehler beim Laden der Issues für %s", proj_data["jira_project_key"])
                    continue

                for jira_issue in all_issues:
                    if jira_issue.get("id") in selected_ids:
                        local_data = jira_issue_to_local(jira_issue, project)
                        _, issue_created = Issue.objects.update_or_create(
                            jira_issue_id=local_data.pop("jira_issue_id"),
                            defaults=local_data,
                        )
                        if issue_created:
                            created_count += 1
                        else:
                            updated_count += 1

        response = ImportConfirmResponseSerializer({
            "created": created_count,
            "updated": updated_count,
            "detail": f"{created_count} erstellt, {updated_count} aktualisiert.",
        })
        return Response(response.data, status=status.HTTP_201_CREATED)


# ─── GitHub Import ────────────────────────────────────────────────────────────


class GitHubImportViewSet(viewsets.ViewSet):
    """GitHub-Repos + Issues voranzeigen und selektiv importieren."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def preview(self, request):
        """Repos des Users mit Issues laden (ohne DB-Write)."""
        integration = _get_integration(request.user, IntegrationConfig.IntegrationType.GITHUB)
        if not integration:
            return Response(
                {"detail": "Keine aktive GitHub-Integration gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.integrations.git.client import GitHubClient

        creds = integration.credentials
        client = GitHubClient(token=creds.get("token", creds.get("access_token", "")))

        mine_only = request.query_params.get("mine_only", "").lower() == "true"
        ck = _cache_key(request.user.id, "github", f"mine={mine_only}")
        cached = cache.get(ck)
        if cached:
            return Response(cached)

        try:
            gh_user = client.get_authenticated_user()
            github_username = gh_user.get("login", "")
        except Exception:
            logger.exception("Fehler beim Laden des GitHub-Users")
            return Response(
                {"detail": "Fehler bei der GitHub-Authentifizierung."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            repos = client.get_repos()
        except Exception:
            logger.exception("Fehler beim Laden der GitHub-Repos")
            return Response(
                {"detail": "Fehler beim Laden der Repositories."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        repos_data = []

        for repo in repos:
            full_name = repo.get("full_name", "")
            owner, repo_name = full_name.split("/", 1) if "/" in full_name else ("", full_name)

            try:
                issues_raw = client.get_issues(owner, repo_name, state="open")
            except Exception:
                logger.warning("Fehler beim Laden der Issues für %s", full_name)
                issues_raw = []

            issues_data = []
            for issue in issues_raw:
                assignee_login = issue.get("assignee", {}).get("login") if issue.get("assignee") else None
                author_login = issue.get("user", {}).get("login") if issue.get("user") else None

                if mine_only and assignee_login != github_username and author_login != github_username:
                    continue

                issues_data.append({
                    "github_id": issue.get("id"),
                    "number": issue.get("number"),
                    "title": issue.get("title", ""),
                    "state": issue.get("state", "open"),
                    "assignee": assignee_login,
                    "author": author_login,
                    "labels": [lbl.get("name", "") for lbl in issue.get("labels", [])],
                    "is_pull_request": "pull_request" in issue,
                })

            repos_data.append({
                "full_name": full_name,
                "description": repo.get("description"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "open_issues_count": repo.get("open_issues_count", 0),
                "issues": issues_data,
            })

        response_data = {
            "repos": repos_data,
            "github_username": github_username,
        }

        serializer = GitHubPreviewResponseSerializer(response_data)
        cache.set(ck, serializer.data, PREVIEW_CACHE_TTL)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def confirm(self, request):
        """Ausgewählte Repos + Issues importieren."""
        serializer = GitHubConfirmRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        integration = _get_integration(request.user, IntegrationConfig.IntegrationType.GITHUB)
        if not integration:
            return Response(
                {"detail": "Keine aktive GitHub-Integration gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.integrations.git.client import GitHubClient
        from apps.integrations.git.mappers import github_issue_to_local

        creds = integration.credentials
        client = GitHubClient(token=creds.get("token", creds.get("access_token", "")))

        created_count = 0
        updated_count = 0

        for repo_data in serializer.validated_data["repos"]:
            full_name = repo_data["full_name"]
            owner, repo_name = full_name.split("/", 1) if "/" in full_name else ("", full_name)

            # Projekt erstellen oder bestehendem zuordnen
            if repo_data.get("create_new_project", True):
                project_name = repo_data.get("project_name") or repo_name
                project, proj_created = Project.objects.update_or_create(
                    github_repo_full_name=full_name,
                    defaults={
                        "name": project_name,
                        "key": _make_project_key(project_name),
                        "source": Project.Source.GITHUB,
                        "owner": request.user,
                    },
                )
                if proj_created:
                    created_count += 1
            else:
                target_id = repo_data.get("target_project_id")
                if not target_id:
                    continue
                try:
                    project = Project.objects.get(id=target_id, owner=request.user)
                    if not project.github_repo_full_name:
                        project.github_repo_full_name = full_name
                        project.save(update_fields=["github_repo_full_name", "updated_at"])
                except Project.DoesNotExist:
                    continue

            # GitHub Issues als lokale Issues importieren
            selected_ids = set(repo_data.get("selected_issue_ids", []))
            if selected_ids:
                try:
                    gh_issues = client.get_issues(owner, repo_name, state="all")
                except Exception:
                    logger.warning("Fehler beim Laden der Issues für %s", full_name)
                    gh_issues = []

                for gh_issue in gh_issues:
                    if gh_issue.get("id") in selected_ids:
                        local_data = github_issue_to_local(gh_issue, project, full_name)
                        github_issue_id = local_data.pop("github_issue_id")
                        _, issue_created = Issue.objects.update_or_create(
                            github_issue_id=github_issue_id,
                            defaults=local_data,
                        )
                        if issue_created:
                            created_count += 1
                        else:
                            updated_count += 1

            # IntegrationConfig.settings.repos aktualisieren
            settings = integration.settings or {}
            repos_config = settings.get("repos", [])
            existing_repos = {r.get("full_name") or f"{r.get('owner')}/{r.get('repo')}" for r in repos_config}
            if full_name not in existing_repos:
                repos_config.append({
                    "owner": owner,
                    "repo": repo_name,
                    "project_id": project.id,
                })
                settings["repos"] = repos_config
                integration.settings = settings
                integration.save(update_fields=["settings", "updated_at"])

        response = ImportConfirmResponseSerializer({
            "created": created_count,
            "updated": updated_count,
            "detail": f"{created_count} erstellt, {updated_count} aktualisiert.",
        })
        return Response(response.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def conflicts(self, request):
        """Konflikte zwischen lokal und GitHub erkennen."""
        integration = _get_integration(request.user, IntegrationConfig.IntegrationType.GITHUB)
        if not integration:
            return Response(
                {"detail": "Keine aktive GitHub-Integration gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.integrations.git.sync import GitHubSyncService

        service = GitHubSyncService(integration)
        all_conflicts = []

        repos = integration.settings.get("repos", [])
        for repo_config in repos:
            owner = repo_config.get("owner", "")
            repo = repo_config.get("repo", "")
            project_id = repo_config.get("project_id")

            if not (owner and repo and project_id):
                continue

            try:
                project = Project.objects.get(id=project_id)
                conflicts = service.detect_conflicts(project, owner, repo)
                all_conflicts.extend(conflicts)
            except Project.DoesNotExist:
                continue
            except Exception as e:
                logger.warning("Fehler bei Konflikterkennung für %s/%s: %s", owner, repo, e)

        return Response({"conflicts": all_conflicts, "count": len(all_conflicts)})


# ─── Import Dashboard ─────────────────────────────────────────────────────────


class ImportDashboardViewSet(viewsets.ViewSet):
    """Import-Historie und Dashboard-Daten."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def history(self, request):
        """Import-Historie: letzte Sync-Logs pro Integration."""
        from apps.integrations.models import SyncLog

        integrations = IntegrationConfig.objects.filter(user=request.user, is_enabled=True)
        history = []

        for integration in integrations:
            latest_logs = SyncLog.objects.filter(
                integration=integration
            ).order_by("-started_at")[:5]

            # Zähle importierte Elemente
            from apps.projects.models import Project as ProjectModel

            if integration.integration_type == "jira":
                item_count = ProjectModel.objects.filter(
                    source="jira", owner=request.user
                ).count()
            elif integration.integration_type == "github":
                item_count = ProjectModel.objects.filter(
                    source="github", owner=request.user
                ).count()
            else:
                from apps.integrations.models import ConfluencePage

                settings = integration.settings or {}
                spaces = settings.get("spaces", [])
                item_count = ConfluencePage.objects.filter(space_key__in=spaces).count() if spaces else 0

            history.append({
                "integration_id": integration.id,
                "integration_type": integration.integration_type,
                "is_enabled": integration.is_enabled,
                "last_synced_at": integration.last_synced_at.isoformat() if integration.last_synced_at else None,
                "sync_status": integration.sync_status,
                "item_count": item_count,
                "poll_interval": (integration.settings or {}).get("poll_interval"),
                "recent_logs": [
                    {
                        "id": log.id,
                        "direction": log.direction,
                        "status": log.status,
                        "records_created": log.records_created,
                        "records_updated": log.records_updated,
                        "errors": log.errors,
                        "started_at": log.started_at.isoformat() if log.started_at else None,
                        "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                    }
                    for log in latest_logs
                ],
            })

        return Response({"integrations": history})

    @action(detail=False, methods=["post"], url_path="update-schedule")
    def update_schedule(self, request):
        """Sync-Intervall für eine Integration aktualisieren."""
        integration_id = request.data.get("integration_id")
        poll_interval = request.data.get("poll_interval")  # in Minuten

        if not integration_id or poll_interval is None:
            return Response(
                {"detail": "integration_id und poll_interval sind erforderlich."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            integration = IntegrationConfig.objects.get(
                id=integration_id, user=request.user
            )
        except IntegrationConfig.DoesNotExist:
            return Response(
                {"detail": "Integration nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        settings = integration.settings or {}
        settings["poll_interval"] = int(poll_interval)
        integration.settings = settings
        integration.save(update_fields=["settings", "updated_at"])

        return Response({"detail": f"Sync-Intervall auf {poll_interval} Minuten gesetzt."})


# ─── Confluence Import ────────────────────────────────────────────────────────


class ConfluenceImportViewSet(viewsets.ViewSet):
    """Confluence-Spaces + Seiten voranzeigen und selektiv importieren."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def preview(self, request):
        """Spaces und/oder Seiten laden (ohne DB-Write)."""
        integration = _get_integration(request.user, IntegrationConfig.IntegrationType.CONFLUENCE)
        if not integration:
            return Response(
                {"detail": "Keine aktive Confluence-Integration gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.integrations.confluence.client import ConfluenceClient

        creds = integration.credentials
        client = ConfluenceClient(url=creds["url"], email=creds["email"], api_token=creds["api_token"])

        space_key = request.query_params.get("space_key")
        my_pages_only = request.query_params.get("my_pages_only", "").lower() == "true"
        user_email = creds.get("email", "")

        if not space_key:
            # Alle Spaces zurückgeben
            try:
                spaces_raw = client.get_spaces()
            except Exception:
                logger.exception("Fehler beim Laden der Confluence-Spaces")
                return Response(
                    {"detail": "Fehler beim Laden der Spaces."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            spaces_data = []
            for space in spaces_raw:
                desc = ""
                if space.get("description", {}).get("plain", {}).get("value"):
                    desc = space["description"]["plain"]["value"]
                spaces_data.append({
                    "key": space.get("key", ""),
                    "name": space.get("name", ""),
                    "description": desc,
                })

            serializer = ConfluencePreviewResponseSerializer({"spaces": spaces_data, "pages": []})
            return Response(serializer.data)

        # Seiten eines Spaces laden
        try:
            pages_raw = client.get_pages(space_key)
        except Exception:
            logger.exception("Fehler beim Laden der Confluence-Seiten für Space %s", space_key)
            return Response(
                {"detail": "Fehler beim Laden der Seiten."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        pages_data = []
        for page in pages_raw:
            version = page.get("version", {})
            author_info = version.get("by", {}) if version else {}
            author_email = author_info.get("email", "")
            author_name = author_info.get("displayName", author_info.get("publicName", ""))

            # History-basierter Author (Ersteller)
            history = page.get("history", {})
            created_by = history.get("createdBy", {})
            creator_email = created_by.get("email", "")

            if my_pages_only and user_email:
                if user_email not in (author_email, creator_email):
                    continue

            pages_data.append({
                "confluence_page_id": page.get("id", ""),
                "title": page.get("title", ""),
                "space_key": space_key,
                "author": author_name or creator_email or None,
                "last_updated": version.get("when"),
                "last_updated_by": author_name or None,
            })

        serializer = ConfluencePreviewResponseSerializer({"spaces": [], "pages": pages_data})
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def confirm(self, request):
        """Ausgewählte Seiten importieren und optional analysieren."""
        serializer = ConfluenceConfirmRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        integration = _get_integration(request.user, IntegrationConfig.IntegrationType.CONFLUENCE)
        if not integration:
            return Response(
                {"detail": "Keine aktive Confluence-Integration gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from apps.integrations.confluence.client import ConfluenceClient

        creds = integration.credentials
        client = ConfluenceClient(url=creds["url"], email=creds["email"], api_token=creds["api_token"])

        created_count = 0
        updated_count = 0
        analyze_page_ids = []

        for page_data in serializer.validated_data["pages"]:
            page_id = page_data["confluence_page_id"]

            # Seiteninhalt holen
            try:
                full_page = client.get_page_content(page_id)
                content_text = full_page.get("plain_text", "")
            except Exception:
                logger.warning("Fehler beim Laden der Seite %s", page_id)
                content_text = ""

            version = full_page.get("version", {}) if "full_page" in dir() else {}
            last_update = version.get("when") if version else None

            page, page_created = ConfluencePage.objects.update_or_create(
                confluence_page_id=page_id,
                defaults={
                    "space_key": page_data["space_key"],
                    "title": page_data["title"],
                    "content_text": content_text,
                    "last_confluence_update": last_update,
                },
            )

            if page_created:
                created_count += 1
            else:
                updated_count += 1

            if page_data.get("analyze", False):
                analyze_page_ids.append(page.id)

        # KI-Analyse für ausgewählte Seiten starten
        if analyze_page_ids:
            from apps.integrations.confluence.tasks import analyze_confluence_page_task

            for page_id in analyze_page_ids:
                analyze_confluence_page_task.delay(page_id)

        # Settings aktualisieren (Spaces merken)
        imported_spaces = {p["space_key"] for p in serializer.validated_data["pages"]}
        settings = integration.settings or {}
        existing_spaces = set(settings.get("spaces", []))
        new_spaces = sorted(existing_spaces | imported_spaces)
        if new_spaces != settings.get("spaces"):
            settings["spaces"] = new_spaces
            integration.settings = settings
            integration.save(update_fields=["settings", "updated_at"])

        response = ImportConfirmResponseSerializer({
            "created": created_count,
            "updated": updated_count,
            "detail": f"{created_count} erstellt, {updated_count} aktualisiert.",
        })
        return Response(response.data, status=status.HTTP_201_CREATED)
