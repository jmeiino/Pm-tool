import logging

from django.utils import timezone

from apps.integrations.models import IntegrationConfig, SyncLog
from apps.projects.models import Issue, Project, Sprint

from .client import JiraClient
from .mappers import jira_issue_to_local, local_issue_to_jira

logger = logging.getLogger(__name__)


class JiraSyncService:
    """Service für die bidirektionale Synchronisierung mit Jira."""

    def __init__(self, integration: IntegrationConfig):
        self.integration = integration
        creds = integration.credentials
        self.client = JiraClient(
            url=creds.get("url", ""),
            email=creds.get("email", ""),
            api_token=creds.get("api_token", ""),
        )

    def sync_projects(self) -> list[Project]:
        """Projekte aus Jira abrufen und lokal aktualisieren."""
        jira_projects = self.client.get_projects()
        synced_projects = []

        for jp in jira_projects:
            project, created = Project.objects.update_or_create(
                jira_project_id=jp.get("id"),
                defaults={
                    "name": jp.get("name", ""),
                    "key": jp.get("key", ""),
                    "jira_project_key": jp.get("key", ""),
                    "is_synced": True,
                    "owner": self.integration.user,
                },
            )
            synced_projects.append(project)
            logger.info(
                "%s Projekt: %s",
                "Erstellt" if created else "Aktualisiert",
                project.key,
            )

        return synced_projects

    def sync_issues(self, project: Project) -> dict:
        """Issues eines Projekts synchronisieren."""
        updated_since = None
        if self.integration.last_synced_at:
            updated_since = self.integration.last_synced_at.strftime("%Y-%m-%d %H:%M")

        jira_issues = self.client.get_issues(
            project.jira_project_key or project.key,
            updated_since=updated_since,
        )

        stats = {"created": 0, "updated": 0}

        for jira_issue in jira_issues:
            mapped = jira_issue_to_local(jira_issue, project)
            jira_id = mapped.pop("jira_issue_id")

            issue, created = Issue.objects.update_or_create(
                jira_issue_id=jira_id,
                defaults=mapped,
            )

            if created:
                stats["created"] += 1
            else:
                stats["updated"] += 1

        return stats

    def sync_inbound(self) -> SyncLog:
        """Kompletter eingehender Sync: Jira -> lokal."""
        sync_log = SyncLog.objects.create(
            integration=self.integration,
            direction=SyncLog.Direction.INBOUND,
            status=SyncLog.Status.STARTED,
            started_at=timezone.now(),
        )

        total_created = 0
        total_updated = 0
        total_processed = 0
        errors = []

        try:
            projects = self.sync_projects()

            for project in projects:
                try:
                    stats = self.sync_issues(project)
                    total_created += stats["created"]
                    total_updated += stats["updated"]
                    total_processed += stats["created"] + stats["updated"]
                except Exception as e:
                    errors.append(f"Fehler bei Projekt {project.key}: {str(e)}")
                    logger.exception("Fehler beim Sync von Projekt %s", project.key)

            sync_log.status = SyncLog.Status.COMPLETED
        except Exception as e:
            sync_log.status = SyncLog.Status.FAILED
            errors.append(str(e))
            logger.exception("Eingehender Jira-Sync fehlgeschlagen")

        sync_log.records_processed = total_processed
        sync_log.records_created = total_created
        sync_log.records_updated = total_updated
        sync_log.errors = errors
        sync_log.completed_at = timezone.now()
        sync_log.save()

        return sync_log

    def sync_outbound(self) -> SyncLog:
        """Kompletter ausgehender Sync: lokal -> Jira."""
        sync_log = SyncLog.objects.create(
            integration=self.integration,
            direction=SyncLog.Direction.OUTBOUND,
            status=SyncLog.Status.STARTED,
            started_at=timezone.now(),
        )

        total_created = 0
        total_updated = 0
        errors = []

        try:
            # Update existing synced issues
            if self.integration.last_synced_at:
                changed_issues = Issue.objects.filter(
                    updated_at__gt=self.integration.last_synced_at,
                    jira_issue_id__isnull=False,
                )
                for issue in changed_issues:
                    try:
                        fields = local_issue_to_jira(issue)
                        self.client.update_issue(issue.jira_issue_key, fields)
                        total_updated += 1
                    except Exception as e:
                        errors.append(f"Fehler beim Update von {issue.key}: {str(e)}")

            # Create new issues in Jira
            new_issues = Issue.objects.filter(
                jira_issue_id__isnull=True,
                project__is_synced=True,
                project__jira_project_key__isnull=False,
            )
            for issue in new_issues:
                try:
                    fields = local_issue_to_jira(issue)
                    result = self.client.create_issue(
                        issue.project.jira_project_key, fields
                    )
                    issue.jira_issue_id = result.get("id")
                    issue.jira_issue_key = result.get("key")
                    issue.save(update_fields=["jira_issue_id", "jira_issue_key", "updated_at"])
                    total_created += 1
                except Exception as e:
                    errors.append(f"Fehler beim Erstellen von {issue.key}: {str(e)}")

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

    def detect_conflicts(self) -> list[dict]:
        """Konflikte zwischen lokalen und Jira-Änderungen erkennen."""
        conflicts = []

        if not self.integration.last_synced_at:
            return conflicts

        # Find issues changed locally since last sync
        local_changed = Issue.objects.filter(
            updated_at__gt=self.integration.last_synced_at,
            jira_issue_id__isnull=False,
            jira_issue_key__isnull=False,
        )

        for issue in local_changed:
            try:
                jira_data = self.client.get_issues(
                    issue.project.jira_project_key or issue.project.key,
                )
                jira_issue = next(
                    (i for i in jira_data if i.get("key") == issue.jira_issue_key),
                    None,
                )
                if not jira_issue:
                    continue

                fields = jira_issue.get("fields", {})
                jira_updated = fields.get("updated")

                # If Jira was also updated since last sync, there's a potential conflict
                if jira_updated and issue.jira_updated_at:
                    from dateutil import parser
                    jira_dt = parser.isoparse(jira_updated)
                    if jira_dt > self.integration.last_synced_at:
                        # Check field-by-field
                        if fields.get("summary", "") != issue.title:
                            conflicts.append({
                                "issue_key": issue.key,
                                "field": "title",
                                "local_value": issue.title,
                                "remote_value": fields.get("summary", ""),
                                "suggestion": "keep_local",
                            })
            except Exception:
                logger.exception("Fehler bei Konflikterkennung für %s", issue.key)

        return conflicts
