import asyncio
import time
import pytest
import respx
import httpx
from unittest.mock import MagicMock, patch

from inotec_kpi_tracker.middleware import DjangoKPIMiddleware, fastapi_kpi_middleware
from inotec_kpi_tracker.sync_client import KPISyncClient
from inotec_kpi_tracker.client import KPIClient
from inotec_kpi_tracker.types import SyncKPIConfig, KPIConfig


# ── Django Middleware ────────────────────────────────────────────────


@pytest.fixture
def sync_client(sync_config: SyncKPIConfig) -> KPISyncClient:
    c = KPISyncClient(sync_config)
    yield c
    c.close()


def test_django_middleware_calls_get_response(sync_client: KPISyncClient):
    get_response = MagicMock(return_value=MagicMock(status_code=200))
    mw = DjangoKPIMiddleware(get_response, client=sync_client)
    request = MagicMock()
    request.path = "/api/test"
    request.method = "GET"
    mw(request)
    get_response.assert_called_once_with(request)


def test_django_middleware_tracks_response_time(sync_client: KPISyncClient):
    get_response = MagicMock(return_value=MagicMock(status_code=200))
    mw = DjangoKPIMiddleware(get_response, client=sync_client)
    request = MagicMock()
    request.path = "/api/test"
    request.method = "GET"
    mw(request)
    assert len(sync_client._queue) >= 1
    events_kpis = [e.kpi_id for e in sync_client._queue]
    assert "performance.ai_provider_latency" in events_kpis or "performance.response_time" in events_kpis


def test_django_middleware_excludes_paths(sync_client: KPISyncClient):
    get_response = MagicMock(return_value=MagicMock(status_code=200))
    mw = DjangoKPIMiddleware(
        get_response,
        client=sync_client,
        exclude_paths=["/health", "/metrics"],
    )
    request = MagicMock()
    request.path = "/health"
    request.method = "GET"
    mw(request)
    assert len(sync_client._queue) == 0


# ── FastAPI/ASGI Middleware ──────────────────────────────────────────


@pytest.fixture
async def async_client_fixture(async_config: KPIConfig) -> KPIClient:
    c = KPIClient(async_config)
    yield c
    await c.close()


async def test_fastapi_middleware_calls_app(async_client_fixture: KPIClient):
    """ASGI middleware passes requests to the wrapped app."""
    called = []

    async def app(scope, receive, send):
        called.append(True)
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    wrapped = fastapi_kpi_middleware(app, client=async_client_fixture)
    scope = {"type": "http", "path": "/api/test", "method": "GET"}
    receive = MagicMock()
    send_messages = []

    async def send(msg):
        send_messages.append(msg)

    await wrapped(scope, receive, send)
    assert called


async def test_fastapi_middleware_excludes_paths(async_client_fixture: KPIClient):
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    wrapped = fastapi_kpi_middleware(
        app,
        client=async_client_fixture,
        exclude_paths=["/health"],
    )
    scope = {"type": "http", "path": "/health", "method": "GET"}

    async def send(msg):
        pass

    await wrapped(scope, MagicMock(), send)
    assert len(async_client_fixture._queue) == 0
