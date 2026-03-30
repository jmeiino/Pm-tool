"""Leichtgewichtiger KPI-Tracking-Client (fire-and-forget)."""

import logging
from datetime import datetime, timezone

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

_client: httpx.Client | None = None


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

    payload = {
        "source": source,
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data or {},
    }

    try:
        response = client.post("/api/events", json=payload)
        if response.status_code >= 400:
            logger.warning("KPI-Event %s fehlgeschlagen: HTTP %s", event, response.status_code)
    except Exception:
        logger.debug("KPI-Tracking nicht erreichbar, Event %s verworfen", event)
