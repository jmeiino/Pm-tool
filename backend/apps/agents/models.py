"""Models für die Integration mit der agentischen Firma."""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class AgentCompanyConfig(TimeStampedModel):
    """Verbindungskonfiguration zur agentischen Firma."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent_companies",
    )
    name = models.CharField(max_length=100, default="Agentic Company")
    base_url = models.CharField(max_length=500, help_text="API-Basis-URL des Agent-Service")
    api_key = models.CharField(max_length=255)
    webhook_secret = models.CharField(max_length=255, help_text="HMAC-Secret für Webhook-Verifizierung")
    is_enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)

    # Paperclip-Integration
    use_paperclip = models.BooleanField(
        default=True,
        help_text="Paperclip als Vermittler nutzen (statt Agent-Agency direkt)",
    )
    paperclip_base_url = models.CharField(
        max_length=500,
        default="http://paperclip-app:3100",
        help_text="Paperclip API-Basis-URL",
    )
    paperclip_company_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Paperclip Company-UUID",
    )
    paperclip_api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="Paperclip Board-API-Key",
    )

    class Meta:
        verbose_name = "Agent Company"
        verbose_name_plural = "Agent Companies"
        unique_together = [("user", "base_url")]

    def __str__(self):
        return f"{self.name} ({self.user})"


class AgentProfile(TimeStampedModel):
    """Ein Agent in der Firma (gespiegelt vom Microservice)."""

    class Role(models.TextChoices):
        CEO = "ceo", "CEO"
        ORCHESTRATOR = "orchestrator", "Orchestrator"
        DEPARTMENT_HEAD = "department_head", "Abteilungsleiter"
        CODER = "coder", "Entwickler"
        WRITER = "writer", "Redakteur"
        RESEARCHER = "researcher", "Rechercheur"
        SPECIALIST = "specialist", "Spezialist"
        QA = "qa", "Qualitätssicherung"

    class Status(models.TextChoices):
        IDLE = "idle", "Verfügbar"
        WORKING = "working", "Arbeitet"
        WAITING = "waiting", "Wartet"
        OFFLINE = "offline", "Offline"

    external_id = models.CharField(max_length=100, unique=True)
    company = models.ForeignKey(AgentCompanyConfig, on_delete=models.CASCADE, related_name="agents")
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=Role.choices)
    department = models.CharField(max_length=100, blank=True)
    avatar_color = models.CharField(max_length=7, default="#6366F1")
    capabilities = models.JSONField(default=list, blank=True)
    ai_provider = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IDLE)

    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"
        ordering = ["role", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class AgentTask(TimeStampedModel):
    """Eine an die agentische Firma delegierte Aufgabe."""

    class Status(models.TextChoices):
        PENDING = "pending", "Wartend"
        ASSIGNED = "assigned", "Zugewiesen"
        IN_PROGRESS = "in_progress", "In Bearbeitung"
        REVIEW = "review", "Review"
        NEEDS_INPUT = "needs_input", "Rückfrage"
        COMPLETED = "completed", "Abgeschlossen"
        FAILED = "failed", "Fehlgeschlagen"
        CANCELLED = "cancelled", "Abgebrochen"

    issue = models.ForeignKey(
        "projects.Issue",
        on_delete=models.CASCADE,
        related_name="agent_tasks",
    )
    company = models.ForeignKey(AgentCompanyConfig, on_delete=models.CASCADE, related_name="tasks")
    external_task_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    assigned_agent = models.ForeignKey(
        AgentProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    priority = models.IntegerField(default=3)
    task_type = models.CharField(max_length=50, blank=True)  # software, content, design, research
    result_summary = models.TextField(blank=True)
    deliverables = models.JSONField(default=list, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Agent Task"
        verbose_name_plural = "Agent Tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task {self.external_task_id} - {self.issue.key}"


class AgentMessage(TimeStampedModel):
    """Eine Nachricht im Agent-Kommunikationskanal."""

    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        DECISION = "decision", "Entscheidung"
        QUESTION = "question", "Rückfrage"
        HANDOFF = "handoff", "Übergabe"
        STATUS_CHANGE = "status_change", "Statusänderung"
        DELIVERABLE = "deliverable", "Ergebnis"
        ERROR = "error", "Fehler"
        SYSTEM = "system", "System"

    task = models.ForeignKey(AgentTask, on_delete=models.CASCADE, related_name="messages")
    sender_agent = models.ForeignKey(
        AgentProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_messages",
    )
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_messages",
    )
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    is_decision_pending = models.BooleanField(default=False)
    parent_message = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies",
    )

    class Meta:
        verbose_name = "Agent Message"
        verbose_name_plural = "Agent Messages"
        ordering = ["created_at"]

    def __str__(self):
        sender = self.sender_agent.name if self.sender_agent else "User"
        return f"[{self.get_message_type_display()}] {sender}: {self.content[:50]}"
