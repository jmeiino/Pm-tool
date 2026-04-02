"""Tests fuer die Agent-Integration: Models, Webhook, API-Endpoints, Paperclip-Bridge."""

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest

from apps.agents.models import AgentCompanyConfig, AgentMessage, AgentProfile, AgentTask
from apps.agents.services import (
    DEFAULT_AGENT_MAPPING,
    PRIORITY_TO_PAPERCLIP,
    AgentBridgeService,
)
from apps.agents.webhook_handler import process_webhook_event, verify_webhook_signature
from tests.factories import IssueFactory, ProjectFactory


@pytest.fixture
def company(user):
    return AgentCompanyConfig.objects.create(
        user=user,
        name="Test Company",
        base_url="https://agents.test.com",
        api_key="test-api-key",
        webhook_secret="test-secret",
        # Paperclip-Felder
        use_paperclip=True,
        paperclip_base_url="http://paperclip-app:3100",
        paperclip_company_id="928540b4-820c-47ad-8505-056bc6235afd",
        paperclip_api_key="pcp_board_test_key",
    )


@pytest.fixture
def legacy_company(user):
    """Company ohne Paperclip — nutzt Legacy-Agent-Agency-API."""
    return AgentCompanyConfig.objects.create(
        user=user,
        name="Legacy Company",
        base_url="https://agents-legacy.test.com",
        api_key="legacy-api-key",
        webhook_secret="legacy-secret",
        use_paperclip=False,
        paperclip_company_id="",
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


@pytest.fixture
def agent_task_with_paperclip_id(company, user):
    """Task mit gespeicherter Paperclip-Issue-ID."""
    project = ProjectFactory(owner=user)
    issue = IssueFactory(project=project)
    return AgentTask.objects.create(
        issue=issue,
        company=company,
        external_task_id="pm-TEST-2-def67890",
        status=AgentTask.Status.IN_PROGRESS,
        priority=2,
        deliverables=[{"paperclip_issue_id": "pcp-issue-uuid-123"}],
    )


# ─── Model Tests ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAgentModels:
    def test_company_creation(self, company):
        assert company.name == "Test Company"
        assert company.is_enabled is True

    def test_company_paperclip_fields(self, company):
        assert company.use_paperclip is True
        assert company.paperclip_company_id == "928540b4-820c-47ad-8505-056bc6235afd"
        assert company.paperclip_base_url == "http://paperclip-app:3100"
        assert company.paperclip_api_key == "pcp_board_test_key"

    def test_legacy_company(self, legacy_company):
        assert legacy_company.use_paperclip is False
        assert legacy_company.paperclip_company_id == ""

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


# ─── AgentBridgeService — Paperclip-Modus ────────────────────────────────────


@pytest.mark.django_db
class TestBridgeServicePaperclip:
    """Tests fuer den Paperclip-Pfad der AgentBridgeService."""

    def test_init_uses_paperclip_client(self, company):
        bridge = AgentBridgeService(company)
        assert bridge._use_paperclip is True
        assert "paperclip-app:3100" in str(bridge.client.base_url)
        bridge.close()

    @patch("apps.agents.services.httpx.Client")
    def test_delegate_creates_paperclip_issue(self, MockClient, company, agent_task):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "pcp-issue-new-uuid",
            "title": agent_task.issue.title,
            "status": "todo",
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        MockClient.return_value = mock_client

        bridge = AgentBridgeService(company)
        bridge.client = mock_client

        result = bridge.delegate_task(agent_task, instructions="Bitte mit Tests")
        assert result["id"] == "pcp-issue-new-uuid"

        # Pruefen, dass der Paperclip-Endpoint aufgerufen wurde
        calls = mock_client.post.call_args_list
        create_call = calls[0]
        assert f"/api/companies/{company.paperclip_company_id}/issues" in create_call.args[0]

        # Payload pruefen
        payload = create_call.kwargs["json"]
        assert payload["title"] == agent_task.issue.title
        assert payload["status"] == "todo"
        assert payload["priority"] == "medium"  # Priority 3 → medium
        assert "ai-agent" in payload["labels"]
        assert "Bitte mit Tests" in payload["description"]
        assert "callback_url" in payload["description"]

    @patch("apps.agents.services.httpx.Client")
    def test_delegate_maps_priority(self, MockClient, company, user):
        """Priority-Mapping: 1→urgent, 2→high, 3→medium, 4→low, 5→low."""
        project = ProjectFactory(owner=user)
        issue = IssueFactory(project=project)

        for pm_prio, expected_pcp in PRIORITY_TO_PAPERCLIP.items():
            task = AgentTask.objects.create(
                issue=issue,
                company=company,
                external_task_id=f"pm-PRIO-{pm_prio}-test",
                priority=pm_prio,
                task_type="software",
            )

            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": f"pcp-{pm_prio}"}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value = mock_client

            bridge = AgentBridgeService(company)
            bridge.client = mock_client
            bridge.delegate_task(task)

            create_call = mock_client.post.call_args_list[0]
            assert create_call.kwargs["json"]["priority"] == expected_pcp
            bridge.close()

    @patch("apps.agents.services.httpx.Client")
    def test_delegate_assigns_agent_by_type(self, MockClient, company, user):
        """Task-Typ → Paperclip-Agent-ID Mapping."""
        project = ProjectFactory(owner=user)
        issue = IssueFactory(project=project)

        for task_type, expected_agent_id in DEFAULT_AGENT_MAPPING.items():
            task = AgentTask.objects.create(
                issue=issue,
                company=company,
                external_task_id=f"pm-TYPE-{task_type}-test",
                priority=3,
                task_type=task_type,
            )

            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": f"pcp-{task_type}"}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value = mock_client

            bridge = AgentBridgeService(company)
            bridge.client = mock_client
            bridge.delegate_task(task)

            create_call = mock_client.post.call_args_list[0]
            assert create_call.kwargs["json"]["assigneeAgentId"] == expected_agent_id
            bridge.close()

    @patch("apps.agents.services.httpx.Client")
    def test_delegate_wakes_agent(self, MockClient, company, agent_task):
        """Nach Issue-Erstellung wird der Agent per Wakeup geweckt."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "pcp-issue-wakeup",
            "assigneeAgentId": "94b76903-93a3-4dd1-aabf-9ca5ef4b281b",
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        MockClient.return_value = mock_client

        agent_task.task_type = "software"
        agent_task.save()

        bridge = AgentBridgeService(company)
        bridge.client = mock_client
        bridge.delegate_task(agent_task)

        # Zweiter post-Aufruf ist der Wakeup
        assert mock_client.post.call_count >= 2
        wakeup_call = mock_client.post.call_args_list[1]
        assert "/api/agents/" in wakeup_call.args[0]
        assert "/wakeup" in wakeup_call.args[0]

    def test_cancel_via_comment(self, company, agent_task_with_paperclip_id):
        """Cancel sendet einen Kommentar auf das Paperclip-Issue."""
        task = agent_task_with_paperclip_id

        with patch.object(AgentBridgeService, "__init__", return_value=None):
            bridge = AgentBridgeService.__new__(AgentBridgeService)
            bridge.company = company
            bridge._use_paperclip = True
            bridge.client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": "comment-1"}
            mock_response.raise_for_status = MagicMock()
            bridge.client.post.return_value = mock_response

            result = bridge.cancel_task(task.external_task_id)
            assert result["id"] == "comment-1"

            call = bridge.client.post.call_args
            assert "/api/issues/pcp-issue-uuid-123/comments" in call.args[0]
            assert "abgebrochen" in call.kwargs["json"]["body"]

    def test_reply_via_comment(self, company, agent_task_with_paperclip_id):
        """Reply sendet einen Kommentar auf das Paperclip-Issue."""
        task = agent_task_with_paperclip_id

        with patch.object(AgentBridgeService, "__init__", return_value=None):
            bridge = AgentBridgeService.__new__(AgentBridgeService)
            bridge.company = company
            bridge._use_paperclip = True
            bridge.client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"id": "comment-reply"}
            mock_response.raise_for_status = MagicMock()
            bridge.client.post.return_value = mock_response

            result = bridge.send_reply(
                task.external_task_id, "Ja, mit Dark Mode", "option_a"
            )
            assert result["id"] == "comment-reply"

            call = bridge.client.post.call_args
            body = call.kwargs["json"]["body"]
            assert "Ja, mit Dark Mode" in body
            assert "option_a" in body

    def test_company_status(self, company):
        """Status-Abruf nutzt Paperclip Agent-Endpunkt."""
        with patch.object(AgentBridgeService, "__init__", return_value=None):
            bridge = AgentBridgeService.__new__(AgentBridgeService)
            bridge.company = company
            bridge._use_paperclip = True
            bridge.client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": "agent-1", "name": "Coder", "status": "working"},
                {"id": "agent-2", "name": "Writer", "status": "idle"},
            ]
            mock_response.raise_for_status = MagicMock()
            bridge.client.get.return_value = mock_response

            result = bridge.get_company_status()
            assert len(result["agents"]) == 2
            assert result["active_tasks"] == 1  # 1 Agent mit status=working

            call = bridge.client.get.call_args
            assert f"/api/companies/{company.paperclip_company_id}/agents" in call.args[0]

    def test_sync_profiles(self, company):
        """Sync liest Agents aus Paperclip und speichert sie."""
        with patch.object(AgentBridgeService, "__init__", return_value=None):
            bridge = AgentBridgeService.__new__(AgentBridgeService)
            bridge.company = company
            bridge._use_paperclip = True
            bridge.client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {
                    "id": "94b76903-93a3-4dd1-aabf-9ca5ef4b281b",
                    "name": "Coder Agent",
                    "status": "idle",
                    "capabilities": ["python", "javascript"],
                },
                {
                    "id": "310c6598-b798-4ef3-bdc2-67e0d275aa5b",
                    "name": "Writer Agent",
                    "status": "idle",
                    "capabilities": ["content", "docs"],
                },
            ]
            mock_response.raise_for_status = MagicMock()
            bridge.client.get.return_value = mock_response

            synced = bridge.sync_agent_profiles()
            assert len(synced) == 2

            coder = AgentProfile.objects.get(
                external_id="94b76903-93a3-4dd1-aabf-9ca5ef4b281b"
            )
            assert coder.role == "coder"
            assert coder.name == "Coder Agent"

            writer = AgentProfile.objects.get(
                external_id="310c6598-b798-4ef3-bdc2-67e0d275aa5b"
            )
            assert writer.role == "writer"


# ─── AgentBridgeService — Legacy-Modus ───────────────────────────────────────


@pytest.mark.django_db
class TestBridgeServiceLegacy:
    """Tests fuer den Legacy-Pfad (direkt Agent-Agency)."""

    def test_init_uses_legacy_client(self, legacy_company):
        bridge = AgentBridgeService(legacy_company)
        assert bridge._use_paperclip is False
        assert "agents-legacy.test.com" in str(bridge.client.base_url)
        bridge.close()

    @patch("apps.agents.services.httpx.Client")
    def test_legacy_delegate(self, MockClient, legacy_company, user):
        project = ProjectFactory(owner=user)
        issue = IssueFactory(project=project)
        task = AgentTask.objects.create(
            issue=issue,
            company=legacy_company,
            external_task_id="pm-LEGACY-1-test",
            priority=2,
            task_type="software",
        )

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "legacy-task-1", "status": "accepted"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        MockClient.return_value = mock_client

        bridge = AgentBridgeService(legacy_company)
        bridge.client = mock_client
        result = bridge.delegate_task(task, instructions="Legacy-Test")

        call = mock_client.post.call_args
        assert "/api/v1/tasks/" in call.args[0]
        payload = call.kwargs["json"]
        assert payload["external_id"] == "pm-LEGACY-1-test"
        assert payload["priority"] == 2  # Kein Paperclip-Mapping
        assert payload["context"]["instructions"] == "Legacy-Test"
        bridge.close()


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
