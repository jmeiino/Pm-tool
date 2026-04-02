import asyncio
import pytest
import respx
import httpx
from inotec_kpi_tracker.client import KPIClient
from inotec_kpi_tracker.types import KPIConfig, KPIEvent


@pytest.fixture
def config() -> KPIConfig:
    return KPIConfig(
        api_url="http://kpi-api:4109/api/v1",
        api_key="test-key",
        app_id="test-app",
        batch_size=3,
        flush_interval=60.0,
    )


@pytest.fixture
async def client(config: KPIConfig) -> KPIClient:
    c = KPIClient(config)
    yield c
    await c.close()


def make_event(**kwargs) -> KPIEvent:
    defaults = dict(
        app_id="test-app",
        event_type="task.completed",
        category="business_impact",
        kpi_id="business_impact.ai_task_completion_rate",
        value=1.0,
    )
    defaults.update(kwargs)
    return KPIEvent(**defaults)


@respx.mock
async def test_track_event_queues_without_sending(client: KPIClient):
    """Events below batch_size are queued but not sent."""
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(202, json={"status": "accepted"})
    )
    await client.track(make_event())
    await client.track(make_event())
    assert len(client._queue) == 2
    assert not route.called


@respx.mock
async def test_flush_sends_queued_events(client: KPIClient):
    """Manual flush sends all queued events."""
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(202, json={"status": "accepted"})
    )
    await client.track(make_event())
    await client.track(make_event())
    await client.flush()
    assert route.called
    payload = route.calls[0].request.content
    import json
    events = json.loads(payload)
    assert len(events) == 2
    assert client._queue == []


@respx.mock
async def test_batch_auto_flushes_at_batch_size(client: KPIClient):
    """Reaching batch_size triggers automatic flush."""
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(202, json={"status": "accepted"})
    )
    # batch_size=3: third event triggers flush
    await client.track(make_event())
    await client.track(make_event())
    await client.track(make_event())
    # Give flush coroutine time to run
    await asyncio.sleep(0.01)
    assert route.called
    assert client._queue == []


@respx.mock
async def test_flush_sends_correct_auth_header(client: KPIClient):
    """Flush sends X-API-Key header."""
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(202, json={"status": "accepted"})
    )
    await client.track(make_event())
    await client.flush()
    assert route.calls[0].request.headers["X-API-Key"] == "test-key"


@respx.mock
async def test_flush_retries_on_server_error(client: KPIClient):
    """Flush retries up to 3 times on 5xx error, then drops events."""
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(500, json={"error": "internal"})
    )
    # Override retry delays to 0 for test speed
    client._retry_delays = [0, 0, 0]
    await client.track(make_event())
    await client.flush()
    assert route.call_count == 3
    # After all retries, queue is cleared (fire-and-forget)
    assert client._queue == []


@respx.mock
async def test_flush_does_not_raise_on_network_error(client: KPIClient):
    """Network errors do not propagate — fire-and-forget."""
    respx.post("http://kpi-api:4109/api/v1/events").mock(
        side_effect=httpx.ConnectError("refused")
    )
    client._retry_delays = [0, 0, 0]
    await client.track(make_event())
    # Must not raise
    await client.flush()
    assert client._queue == []


@respx.mock
async def test_close_flushes_remaining_events(client: KPIClient):
    """close() flushes remaining events before closing the http client."""
    route = respx.post("http://kpi-api:4109/api/v1/events").mock(
        return_value=httpx.Response(202, json={"status": "accepted"})
    )
    await client.track(make_event())
    await client.close()
    assert route.called
