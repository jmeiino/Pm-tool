import logging

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.integrations.models import IntegrationConfig

from .graph_client import GraphClient

logger = logging.getLogger(__name__)

DEFAULT_SCOPES = [
    "Calendars.Read",
    "Mail.Read",
    "Tasks.Read",
    "ChannelMessage.Read.All",
]


def _get_graph_client() -> GraphClient:
    return GraphClient(
        client_id=settings.MS_CLIENT_ID,
        client_secret=settings.MS_CLIENT_SECRET,
        tenant_id=settings.MS_TENANT_ID,
        redirect_uri=settings.MS_REDIRECT_URI,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def microsoft_auth_start(request):
    """OAuth2-Autorisierung starten — gibt Auth-URL zurück."""
    client = _get_graph_client()
    auth_url = client.get_auth_url(DEFAULT_SCOPES)

    # Store auth flow in session for callback validation
    request.session["ms_auth_flow"] = client._auth_flow

    return Response({"auth_url": auth_url})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def microsoft_auth_callback(request):
    """OAuth2-Callback — speichert Token in IntegrationConfig."""
    client = _get_graph_client()
    client._auth_flow = request.session.get("ms_auth_flow", {})

    auth_response = {
        "code": request.query_params.get("code", ""),
        "state": request.query_params.get("state", ""),
    }

    result = client.acquire_token(auth_response, DEFAULT_SCOPES)

    if "error" in result:
        return Response(
            {"detail": f"Authentifizierung fehlgeschlagen: {result.get('error_description', '')}"},
            status=400,
        )

    # Save tokens
    IntegrationConfig.objects.update_or_create(
        user=request.user,
        integration_type=IntegrationConfig.IntegrationType.MICROSOFT_CALENDAR,
        defaults={
            "credentials": {
                "access_token": result.get("access_token", ""),
                "refresh_token": result.get("refresh_token", ""),
                "token_type": result.get("token_type", ""),
            },
            "is_enabled": True,
        },
    )

    # Clean up session
    request.session.pop("ms_auth_flow", None)

    return Response({"detail": "Microsoft 365 erfolgreich verbunden."})
