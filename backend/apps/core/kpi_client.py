"""Leichtgewichtiger KPI-Tracking-Client (fire-and-forget).

Sendet Events im KPI-Tracking v1 Batch-Format:
  POST /api/v1/events  — Array von Event-Objekten mit event_id, app_id,
  event_type, category, kpi_id, value, timestamp.
"""

import logging
import uuid
from datetime import datetime, timezone

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

_client: httpx.Client | None = None

# Mapping von Event-Namen zu KPI-Tracking Kategorien
_EVENT_CATEGORIES = {
    "project.created": "usage",
    "project.issue_created": "usage",
    "todo.created": "usage",
    "integration.sync": "usage",
    "agent.task_delegated": "usage",
    "test.ping": "usage",
}


def _get_client() -> httpx.Client | None:
    """Lazy-initialisierter HTTP-Client fuer KPI-Tracking."""
    global _client
    kpi_url = getattr(settings, "KPI_API_URL", "")
    if not kpi_url:
        return None
    if _client is None:
        _client = httpx.Client(
            base_url=kpi_url,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": getattr(settings, "KPI_API_KEY", ""),
            },
            timeout=5.0,
        )
    return _client


def track_event(event: str, data: dict | None = None, source: str = "pm-tool"):
    """Event an KPI-Tracking senden (fire-and-forget).

    Fehler werden geloggt, blockieren aber nie den Hauptprozess.
    """
    client = _get_client()
    if not client:
        return

    category = _EVENT_CATEGORIES.get(event, "usage")
    payload = [
        {
            "event_id": str(uuid.uuid4()),
            "app_id": source,
            "environment": "development",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "event_type": event,
            "category": category,
            "kpi_id": event,
            "value": 1,
            "metadata": data or {},
        }
    ]

    try:
        response = client.post("/api/v1/events", json=payload)
        if response.status_code >= 400:
            logger.warning("KPI-Event %s fehlgeschlagen: HTTP %s", event, response.status_code)
    except Exception:
        logger.debug("KPI-Tracking nicht erreichbar, Event %s verworfen", event)
