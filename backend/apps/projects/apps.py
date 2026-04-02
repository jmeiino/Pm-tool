from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.projects"
    verbose_name = "Projekte"

    def ready(self):
        from apps.projects.models import Issue
        from apps.kpi.signals import connect_issue_signals
        connect_issue_signals(Issue)
