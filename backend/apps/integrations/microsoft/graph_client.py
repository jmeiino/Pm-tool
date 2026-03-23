import logging

import httpx
import msal

logger = logging.getLogger(__name__)


class GraphClient:
    """Client für die Microsoft Graph API mit MSAL-Authentifizierung."""

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(self, client_id: str, client_secret: str, tenant_id: str, redirect_uri: str):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.redirect_uri = redirect_uri
        self.app = msal.ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
        )
        self._access_token = None
        self._auth_flow = None

    def get_auth_url(self, scopes: list[str]) -> str:
        """OAuth2-Autorisierungs-URL generieren."""
        self._auth_flow = self.app.initiate_auth_code_flow(
            scopes,
            redirect_uri=self.redirect_uri,
        )
        return self._auth_flow["auth_uri"]

    def acquire_token(self, auth_response: dict, scopes: list[str]) -> dict:
        """Access-Token mit Authorization Code abrufen."""
        result = self.app.acquire_token_by_auth_code_flow(
            self._auth_flow or {},
            auth_response,
        )
        if "access_token" in result:
            self._access_token = result["access_token"]
        return result

    def set_token(self, access_token: str):
        """Access-Token direkt setzen (aus gespeicherten Credentials)."""
        self._access_token = access_token

    def refresh_token(self, refresh_token_val: str, scopes: list[str]) -> dict:
        """Access-Token mit Refresh-Token erneuern."""
        result = self.app.acquire_token_by_refresh_token(refresh_token_val, scopes)
        if "access_token" in result:
            self._access_token = result["access_token"]
        return result

    def _request(self, method: str, url: str, **kwargs) -> dict:
        """HTTP-Request an Graph API mit Bearer Token."""
        if not self._access_token:
            raise ValueError("Kein Access-Token vorhanden")

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        full_url = f"{self.GRAPH_BASE}{url}" if url.startswith("/") else url

        with httpx.Client(timeout=30.0) as client:
            response = client.request(method, full_url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}

    def _paginate(self, url: str, params: dict | None = None) -> list[dict]:
        """Paginierte Graph-API-Anfrage."""
        all_items = []
        current_url = f"{self.GRAPH_BASE}{url}"

        while current_url:
            if not self._access_token:
                raise ValueError("Kein Access-Token vorhanden")

            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    current_url,
                    headers={"Authorization": f"Bearer {self._access_token}"},
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

            all_items.extend(data.get("value", []))
            current_url = data.get("@odata.nextLink")
            params = None  # nextLink already contains params

        return all_items

    def get_calendar_events(self, start: str, end: str) -> list[dict]:
        """Kalender-Termine in einem Zeitraum abrufen."""
        return self._paginate(
            "/me/calendarView",
            params={
                "startDateTime": start,
                "endDateTime": end,
                "$orderby": "start/dateTime",
                "$top": "100",
            },
        )

    def get_emails(self, folder: str = "inbox", top: int = 50) -> list[dict]:
        """E-Mails aus einem Ordner abrufen."""
        return self._request(
            "GET",
            f"/me/mailFolders/{folder}/messages",
            params={"$top": str(top), "$orderby": "receivedDateTime desc"},
        ).get("value", [])

    def get_teams_channels(self, team_id: str) -> list[dict]:
        """Kanäle eines Teams abrufen."""
        return self._request("GET", f"/teams/{team_id}/channels").get("value", [])

    def get_channel_messages(self, team_id: str, channel_id: str) -> list[dict]:
        """Nachrichten eines Kanals abrufen."""
        return self._paginate(f"/teams/{team_id}/channels/{channel_id}/messages")

    def get_todo_lists(self) -> list[dict]:
        """To-Do-Listen abrufen."""
        return self._request("GET", "/me/todo/lists").get("value", [])

    def get_todo_tasks(self, list_id: str) -> list[dict]:
        """Aufgaben einer To-Do-Liste abrufen."""
        return self._paginate(f"/me/todo/lists/{list_id}/tasks")
