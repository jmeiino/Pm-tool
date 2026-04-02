"""Django Middleware fuer automatisches KPI-Event-Tracking."""

import logging
import re

from .kpi_client import track_event

logger = logging.getLogger(__name__)

# Patterns fuer Events die automatisch getrackt werden
_TRACK_PATTERNS = [
    (re.compile(r"^POST /api/v1/projects/$"), "project.created"),
    (re.compile(r"^POST /api/v1/projects/\d+/issues/$"), "project.issue_created"),
    (re.compile(r"^POST /api/v1/todos/$"), "todo.created"),
    (re.compile(r"^POST /api/v1/integrations/configs/\d+/sync/$"), "integration.sync"),
    (re.compile(r"^POST /api/v1/agents/tasks/delegate/$"), "agent.task_delegated"),
]


class KPITrackingMiddleware:
    """Trackt erfolgreiche API-Mutationen als KPI-Events."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Nur erfolgreiche POST/PUT/PATCH tracken
        if request.method not in ("POST", "PUT", "PATCH"):
            return response
        if response.status_code >= 400:
            return response

        path_key = f"{request.method} {request.path}"
        for pattern, event_name in _TRACK_PATTERNS:
            if pattern.match(path_key):
                user_id = getattr(request.user, "id", None)
                track_event(event_name, {
                    "user_id": user_id,
                    "path": request.path,
                    "status_code": response.status_code,
                })
                break

        return response
