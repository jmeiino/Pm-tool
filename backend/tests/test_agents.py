"""Tests für die Agent-Integration: Models, Webhook, API-Endpoints."""

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest

from apps.agents.models import AgentCompanyConfig, AgentMessage, AgentProfile, AgentTask
from apps.agents.webhook_handler import process_webhook_event, verify_webhook_signature
from tests.factories import IssueFactory, ProjectFactory, UserFactory


@pytest.fixture
def company(user):
    return AgentCompanyConfig.objects.create(
        user=user,
        name="Test Company",
        base_url="https://agents.test.com",
        api_key="test-api-key",
        webhook_secret="test-secret",
    )


@pytest.fixture
def agent(company):
    return AgentProfile.objects.create(
        external_id="agent-ceo-01",
        company=company,
        name="CEO Agent",
        role=AgentProfile.Role.CEO,
        department="Management",
        avatar_color="#6366F1",
    )


@pytest.fixture
def agent_task(company, user):
    project = ProjectFactory(owner=user)
    issue = IssueFactory(project=project)
    return AgentTask.objects.create(
        issue=issue,
        company=company,
        external_task_id="pm-TEST-1-abc12345",
        status=AgentTask.Status.IN_PROGRESS,
        priority=3,
    )


# ─── Model Tests ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAgentModels:
    def test_company_creation(self, company):
        assert company.name == "Test Company"
        assert company.is_enabled is True

    def test_agent_profile(self, agent):
        assert agent.role == "ceo"
        assert str(agent) == "CEO Agent (CEO)"

    def test_agent_task(self, agent_task):
        assert agent_task.status == "in_progress"
        assert "pm-TEST" in agent_task.external_task_id

    def test_agent_message(self, agent_task, agent):
        msg = AgentMessage.objects.create(
            task=agent_task,
            sender_agent=agent,
            message_type=AgentMessage.MessageType.TEXT,
            content="Ich beginne mit der Arbeit.",
        )
        assert msg.sender_agent == agent
        assert msg.sender_user is None


# ─── Webhook Tests ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestWebhookHandler:
    def test_verify_signature_valid(self):
        secret = "test-secret"
        body = b'{"event_type": "test"}'
        sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert verify_webhook_signature(body, sig, secret) is True

    def test_verify_signature_invalid(self):
        assert verify_webhook_signature(b"body", "sha256=wrong", "secret") is False

    def test_process_agent_message(self, agent_task, company):
        event = {
            "event_type": "agent.message",
            "task_id": agent_task.external_task_id,
            "payload": {
                "sender_agent_id": "agent-dev-01",
                "sender_name": "Dev Agent",
                "sender_role": "specialist",
                "message_type": "text",
                "content": "Ich arbeite am Feature.",
                "metadata": {},
            },
        }
        result = process_webhook_event(event, company)
        assert result["status"] == "ok"
        assert AgentMessage.objects.filter(task=agent_task).count() == 1

        msg = AgentMessage.objects.get(task=agent_task)
        assert msg.content == "Ich arbeite am Feature."
        assert msg.sender_agent is not None
        assert msg.sender_agent.name == "Dev Agent"

    def test_process_status_change(self, agent_task, company):
        event = {
            "event_type": "task.status_changed",
            "task_id": agent_task.external_task_id,
            "payload": {"status": "review"},
        }
        result = process_webhook_event(event, company)
        assert result["status"] == "ok"

        agent_task.refresh_from_db()
        assert agent_task.status == "review"

    def test_process_task_completed(self, agent_task, company):
        event = {
            "event_type": "task.completed",
            "task_id": agent_task.external_task_id,
            "payload": {
                "status": "completed",
                "result_summary": "Feature implementiert und getestet.",
            },
        }
        result = process_webhook_event(event, company)
        assert result["status"] == "ok"

        agent_task.refresh_from_db()
        assert agent_task.status == "completed"
        assert agent_task.result_summary == "Feature implementiert und getestet."

    def test_process_unknown_task(self, company):
        event = {
            "event_type": "agent.message",
            "task_id": "nonexistent",
            "payload": {"content": "test"},
        }
        result = process_webhook_event(event, company)
        assert result["status"] == "error"

    def test_process_unknown_event(self, company):
        event = {"event_type": "unknown.event", "task_id": "x", "payload": {}}
        result = process_webhook_event(event, company)
        assert result["status"] == "ignored"


# ─── API Tests ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAgentTaskAPI:
    def test_list_tasks(self, api_client, agent_task):
        response = api_client.get("/api/v1/agents/tasks/")
        assert response.status_code == 200

    def test_retrieve_task(self, api_client, agent_task):
        response = api_client.get(f"/api/v1/agents/tasks/{agent_task.id}/")
        assert response.status_code == 200
        assert response.data["external_task_id"] == agent_task.external_task_id

    @patch("apps.agents.views.AgentBridgeService")
    def test_delegate_task(self, MockBridge, api_client, user, company):
        mock_bridge = MagicMock()
        MockBridge.return_value.__enter__ = MagicMock(return_value=mock_bridge)
        MockBridge.return_value.__exit__ = MagicMock(return_value=False)

        project = ProjectFactory(owner=user)
        issue = IssueFactory(project=project)

        response = api_client.post(
            "/api/v1/agents/tasks/delegate/",
            {"issue_id": issue.id, "task_type": "software", "priority": 2},
            format="json",
        )
        assert response.status_code == 201
        assert AgentTask.objects.filter(issue=issue).exists()
        mock_bridge.delegate_task.assert_called_once()

    def test_delegate_without_company(self, api_client, user):
        project = ProjectFactory(owner=user)
        issue = IssueFactory(project=project)

        response = api_client.post(
            "/api/v1/agents/tasks/delegate/",
            {"issue_id": issue.id},
            format="json",
        )
        assert response.status_code == 404

    @patch("apps.agents.views.AgentBridgeService")
    def test_reply_to_agent(self, MockBridge, api_client, agent_task):
        mock_bridge = MagicMock()
        MockBridge.return_value.__enter__ = MagicMock(return_value=mock_bridge)
        MockBridge.return_value.__exit__ = MagicMock(return_value=False)

        response = api_client.post(
            f"/api/v1/agents/tasks/{agent_task.id}/reply/",
            {"content": "Ja, bitte mit Dark Mode."},
            format="json",
        )
        assert response.status_code == 200
        assert AgentMessage.objects.filter(
            task=agent_task, sender_user__isnull=False
        ).exists()

    def test_cancel_task(self, api_client, agent_task):
        response = api_client.post(f"/api/v1/agents/tasks/{agent_task.id}/cancel/")
        assert response.status_code == 200

        agent_task.refresh_from_db()
        assert agent_task.status == "cancelled"

    def test_cancel_completed_task(self, api_client, agent_task):
        agent_task.status = AgentTask.Status.COMPLETED
        agent_task.save()

        response = api_client.post(f"/api/v1/agents/tasks/{agent_task.id}/cancel/")
        assert response.status_code == 400


@pytest.mark.django_db
class TestAgentProfileAPI:
    def test_list_profiles(self, api_client, agent):
        response = api_client.get("/api/v1/agents/profiles/")
        assert response.status_code == 200

    def test_retrieve_profile(self, api_client, agent):
        response = api_client.get(f"/api/v1/agents/profiles/{agent.id}/")
        assert response.status_code == 200
        assert response.data["name"] == "CEO Agent"


@pytest.mark.django_db
class TestWebhookEndpoint:
    def test_webhook_valid_signature(self, api_client, company, agent_task):
        body = json.dumps({
            "event_type": "agent.message",
            "task_id": agent_task.external_task_id,
            "payload": {
                "sender_agent_id": "agent-01",
                "sender_name": "Test",
                "message_type": "text",
                "content": "Hello",
            },
        }).encode()
        sig = "sha256=" + hmac.new(
            company.webhook_secret.encode(), body, hashlib.sha256
        ).hexdigest()

        response = api_client.post(
            "/api/v1/agents/webhooks/event/",
            data=body,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=sig,
        )
        assert response.status_code == 200

    def test_webhook_invalid_signature(self, api_client, company):
        response = api_client.post(
            "/api/v1/agents/webhooks/event/",
            data=b'{}',
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE="sha256=invalid",
        )
        assert response.status_code == 401
