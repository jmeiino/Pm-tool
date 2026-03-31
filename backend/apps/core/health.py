"""Health-Check Endpoint fuer Monitoring und Load-Balancer."""

import logging

from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def health_check(request):
    """Prüft DB-Verbindung und gibt Status zurück."""
    checks = {"database": False, "status": "unhealthy"}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        logger.warning("Health-Check: Datenbank nicht erreichbar")

    if checks["database"]:
        checks["status"] = "healthy"
        return JsonResponse(checks, status=200)

    return JsonResponse(checks, status=503)
