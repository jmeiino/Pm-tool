from __future__ import annotations
import asyncio
import logging
from typing import Any

import httpx

from .types import KPIConfig, KPIEvent

logger = logging.getLogger(__name__)

_DEFAULT_RETRY_DELAYS = [1.0, 2.0, 4.0]


class KPIClient:
    """Async KPI client for FastAPI / asyncio applications."""

    def __init__(self, config: KPIConfig) -> None:
        self._config = config
        self._queue: list[KPIEvent] = []
        self._flushing = False
        self._closed = False
        self._retry_delays = list(_DEFAULT_RETRY_DELAYS)
        self._http = httpx.AsyncClient(
            headers={
                "X-API-Key": config.api_key,
                "Content-Type": "application/json",
            },
            timeout=5.0,
        )
        self._timer: asyncio.TimerHandle | None = None
        self._schedule_flush()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def track(self, event: KPIEvent) -> None:
        """Enqueue an event. Flushes immediately when batch_size is reached."""
        if self._closed:
            return
        self._queue.append(event)
        if len(self._queue) >= self._config.batch_size:
            await self._flush_nowait()

    async def flush(self) -> None:
        """Send all queued events to the API."""
        await self._do_flush()

    async def close(self) -> None:
        """Flush remaining events and close the HTTP client."""
        self._closed = True
        if self._timer is not None:
            self._timer.cancel()
        await self._do_flush()
        await self._http.aclose()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _schedule_flush(self) -> None:
        """Schedule next periodic flush."""
        if self._closed:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._timer = loop.call_later(
            self._config.flush_interval, lambda: asyncio.ensure_future(self._flush_nowait())
        )

    async def _flush_nowait(self) -> None:
        asyncio.ensure_future(self._do_flush())

    async def _do_flush(self) -> None:
        if self._flushing or not self._queue:
            return
        self._flushing = True
        events, self._queue = self._queue, []
        try:
            await self._send_with_retry(events)
        finally:
            self._flushing = False
            self._schedule_flush()

    async def _send_with_retry(self, events: list[KPIEvent]) -> None:
        payload = [e.to_dict() for e in events]
        url = f"{self._config.api_url}/events"
        for attempt, delay in enumerate(self._retry_delays):
            try:
                response = await self._http.post(url, json=payload)
                if response.status_code < 500:
                    return
                logger.warning(
                    "KPI API returned %s (attempt %d/3)",
                    response.status_code,
                    attempt + 1,
                )
            except Exception as exc:
                logger.warning("KPI send failed (attempt %d/3): %s", attempt + 1, exc)
            if delay > 0 and attempt < len(self._retry_delays) - 1:
                await asyncio.sleep(delay)
        logger.error("KPI events dropped after 3 failed attempts")
