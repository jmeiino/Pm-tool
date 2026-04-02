from __future__ import annotations
import time
import logging
from typing import Any, Callable

from .types import KPIEvent
from .sync_client import KPISyncClient
from .client import KPIClient

logger = logging.getLogger(__name__)


class DjangoKPIMiddleware:
    """Django WSGI middleware that tracks HTTP response time per request."""

    def __init__(
        self,
        get_response: Callable,
        client: KPISyncClient,
        exclude_paths: list[str] | None = None,
    ) -> None:
        self._get_response = get_response
        self._client = client
        self._exclude_paths = exclude_paths or []

    def __call__(self, request: Any) -> Any:
        path: str = getattr(request, "path", "")
        if any(path.startswith(p) for p in self._exclude_paths):
            return self._get_response(request)

        start = time.perf_counter()
        response = self._get_response(request)
        duration_ms = (time.perf_counter() - start) * 1000

        try:
            self._client.track(KPIEvent(
                app_id=self._client._config.app_id,
                event_type="http.response_time",
                category="performance",
                kpi_id="performance.response_time",
                value=round(duration_ms, 2),
                unit="ms",
                dimensions={
                    "method": getattr(request, "method", "UNKNOWN"),
                    "path": path,
                    "status": getattr(response, "status_code", 0),
                },
            ))
        except Exception as exc:
            logger.debug("KPI middleware error: %s", exc)

        return response


def fastapi_kpi_middleware(
    app: Any,
    client: KPIClient,
    exclude_paths: list[str] | None = None,
) -> Any:
    """
    ASGI middleware factory for FastAPI / Starlette.

    Usage:
        app = FastAPI()
        app = fastapi_kpi_middleware(app, client=kpi_client)
    """
    _exclude = exclude_paths or []

    async def middleware(scope: dict, receive: Any, send: Any) -> None:
        if scope.get("type") != "http":
            await app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        if any(path.startswith(p) for p in _exclude):
            await app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 200

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message.get("type") == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        try:
            await app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            try:
                await client.track(KPIEvent(
                    app_id=client._config.app_id,
                    event_type="http.response_time",
                    category="performance",
                    kpi_id="performance.response_time",
                    value=round(duration_ms, 2),
                    unit="ms",
                    dimensions={
                        "method": scope.get("method", "UNKNOWN"),
                        "path": path,
                        "status": status_code,
                    },
                ))
            except Exception as exc:
                logger.debug("KPI middleware error: %s", exc)

    return middleware
