import logging
import secrets

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubClient:
    """Client für die GitHub REST API mit httpx."""

    def __init__(self, token: str = "", access_token: str = ""):
        self.access_token = token or access_token
        self.client = httpx.Client(
            base_url=GITHUB_API_BASE,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    def _paginate(self, url: str, params: dict | None = None) -> list[dict]:
        """Paginierte GitHub-API-Anfrage über Link-Header."""
        all_items = []
        params = params or {}
        params.setdefault("per_page", "100")

        while url:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            all_items.extend(response.json())

            # Follow Link header for next page
            link = response.headers.get("Link", "")
            url = ""
            params = None  # URL already contains params
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.split("<")[1].split(">")[0]

        return all_items

    def get_repos(self, org: str | None = None) -> list[dict]:
        """Repositories abrufen (eigene oder einer Organisation)."""
        url = f"/orgs/{org}/repos" if org else "/user/repos"
        return self._paginate(url)

    def get_commits(self, owner: str, repo: str, since: str | None = None) -> list[dict]:
        """Commits eines Repositories abrufen."""
        params: dict = {}
        if since:
            params["since"] = since
        return self._paginate(f"/repos/{owner}/{repo}/commits", params)

    def get_pull_requests(self, owner: str, repo: str, state: str = "all") -> list[dict]:
        """Pull Requests abrufen."""
        return self._paginate(f"/repos/{owner}/{repo}/pulls", {"state": state})

    def get_issues(self, owner: str, repo: str, state: str = "all") -> list[dict]:
        """Issues abrufen (ohne PRs)."""
        all_items = self._paginate(f"/repos/{owner}/{repo}/issues", {"state": state})
        return [item for item in all_items if "pull_request" not in item]

    def get_repo(self, owner: str, repo: str) -> dict:
        """Repository-Metadaten abrufen."""
        response = self.client.get(f"/repos/{owner}/{repo}")
        response.raise_for_status()
        return response.json()

    def get_readme(self, owner: str, repo: str) -> str:
        """README-Inhalt als Text abrufen."""
        try:
            response = self.client.get(
                f"/repos/{owner}/{repo}/readme",
                headers={"Accept": "application/vnd.github.raw+json"},
            )
            response.raise_for_status()
            return response.text[:10000]
        except httpx.HTTPStatusError:
            return ""

    def get_languages(self, owner: str, repo: str) -> dict:
        """Sprachverteilung (Bytes pro Sprache) abrufen."""
        response = self.client.get(f"/repos/{owner}/{repo}/languages")
        response.raise_for_status()
        return response.json()

    def get_contributors(self, owner: str, repo: str, limit: int = 10) -> list[dict]:
        """Top-Contributors abrufen."""
        response = self.client.get(
            f"/repos/{owner}/{repo}/contributors",
            params={"per_page": str(limit)},
        )
        response.raise_for_status()
        return response.json()

    def get_webhooks(self, owner: str, repo: str) -> list[dict]:
        """Vorhandene Webhooks abrufen."""
        response = self.client.get(f"/repos/{owner}/{repo}/hooks")
        response.raise_for_status()
        return response.json()

    def create_webhook(self, owner: str, repo: str, callback_url: str, events: list[str]) -> dict:
        """Webhook für Repository-Events erstellen."""
        webhook_secret = secrets.token_hex(32)
        payload = {
            "config": {
                "url": callback_url,
                "content_type": "json",
                "secret": webhook_secret,
            },
            "events": events,
            "active": True,
        }
        response = self.client.post(f"/repos/{owner}/{repo}/hooks", json=payload)
        response.raise_for_status()
        result = response.json()
        result["secret"] = webhook_secret
        return result

    def close(self):
        """HTTP-Client schließen."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
