from __future__ import annotations

import atexit
import logging
from typing import Any

from django.conf import settings

from inotec_kpi_tracker import KPISyncClient, SyncKPIConfig, KPIEvent

logger = logging.getLogger(__name__)

_client: KPISyncClient | None = None


def get_kpi_client() -> KPISyncClient | None:
    global _client
    if _client is not None:
        return _client

    url = getattr(settings, "KPI_TRACKING_URL", "") or getattr(settings, "KPI_API_URL", "")
    key = getattr(settings, "KPI_API_KEY", "")
    if not url or not key:
        return None

    _client = KPISyncClient(SyncKPIConfig(
        api_url=url,
        api_key=key,
        app_id="pm-tool",
        batch_size=50,
        flush_interval=10.0,
    ))
    atexit.register(_client.close)
    return _client


def track_kpi(
    event_type: str,
    category: str,
    kpi_id: str,
    value: float,
    unit: str = "count",
    dimensions: dict[str, Any] | None = None,
) -> None:
    try:
        client = get_kpi_client()
        if client is None:
            return
        client.track(KPIEvent(
            app_id="pm-tool",
            event_type=event_type,
            category=category,
            kpi_id=kpi_id,
            value=value,
            unit=unit,
            dimensions=dimensions,
        ))
    except Exception:
        logger.debug("KPI event %s could not be tracked", event_type, exc_info=True)
