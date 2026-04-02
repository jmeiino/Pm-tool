from __future__ import annotations
import logging
import threading
import time

import httpx

from .types import SyncKPIConfig, KPIEvent

logger = logging.getLogger(__name__)

_DEFAULT_RETRY_DELAYS = [1.0, 2.0, 4.0]


class KPISyncClient:
    """Synchronous KPI client for Django / WSGI applications."""

    def __init__(self, config: SyncKPIConfig) -> None:
        self._config = config
        self._queue: list[KPIEvent] = []
        self._lock = threading.Lock()
        self._flushing = False
        self._closed = False
        self._retry_delays = list(_DEFAULT_RETRY_DELAYS)
        self._http = httpx.Client(
            headers={
                "X-API-Key": config.api_key,
                "Content-Type": "application/json",
            },
            timeout=5.0,
        )
        self._timer: threading.Timer | None = None
        self._schedule_flush()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def track(self, event: KPIEvent) -> None:
        """Enqueue an event. Triggers background flush when batch_size is reached."""
        if self._closed:
            return
        with self._lock:
            self._queue.append(event)
            should_flush = len(self._queue) >= self._config.batch_size
        if should_flush:
            t = threading.Thread(target=self._do_flush, daemon=True)
            t.start()

    def flush(self) -> None:
        """Synchronously send all queued events."""
        self._do_flush()

    def close(self) -> None:
        """Flush remaining events and close the HTTP client."""
        self._closed = True
        if self._timer is not None:
            self._timer.cancel()
        self._do_flush()
        self._http.close()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _schedule_flush(self) -> None:
        if self._closed:
            return
        self._timer = threading.Timer(self._config.flush_interval, self._timer_flush)
        self._timer.daemon = True
        self._timer.start()

    def _timer_flush(self) -> None:
        self._do_flush()
        self._schedule_flush()

    def _do_flush(self) -> None:
        with self._lock:
            if self._flushing or not self._queue:
                return
            self._flushing = True
            events, self._queue = self._queue, []
        try:
            self._send_with_retry(events)
        finally:
            with self._lock:
                self._flushing = False

    def _send_with_retry(self, events: list[KPIEvent]) -> None:
        payload = [e.to_dict() for e in events]
        url = f"{self._config.api_url}/events"
        for attempt, delay in enumerate(self._retry_delays):
            try:
                response = self._http.post(url, json=payload)
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
                time.sleep(delay)
        logger.error("KPI events dropped after %d failed attempts", len(self._retry_delays))
