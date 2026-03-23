import logging
import re

from atlassian import Confluence

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Client für die Kommunikation mit der Confluence REST API."""

    def __init__(self, url: str, email: str, api_token: str):
        self.url = url
        self.email = email
        self.confluence = Confluence(
            url=url,
            username=email,
            password=api_token,
            cloud=True,
        )

    def get_spaces(self) -> list[dict]:
        """Alle verfügbaren Spaces abrufen."""
        try:
            result = self.confluence.get_all_spaces(start=0, limit=50, expand="description.plain")
            return result.get("results", [])
        except Exception:
            logger.exception("Fehler beim Abrufen der Confluence-Spaces")
            raise

    def get_pages(self, space_key: str) -> list[dict]:
        """Seiten eines Spaces abrufen."""
        try:
            pages = self.confluence.get_all_pages_from_space(
                space_key, start=0, limit=100, expand="body.storage,version"
            )
            return pages
        except Exception:
            logger.exception("Fehler beim Abrufen der Seiten für Space %s", space_key)
            raise

    def get_page_content(self, page_id: str) -> dict:
        """Inhalt einer einzelnen Seite abrufen."""
        try:
            page = self.confluence.get_page_by_id(page_id, expand="body.storage,version")
            # Strip HTML tags for plain text
            html = page.get("body", {}).get("storage", {}).get("value", "")
            plain = self._html_to_text(html)
            page["plain_text"] = plain
            return page
        except Exception:
            logger.exception("Fehler beim Abrufen der Seite %s", page_id)
            raise

    def create_page(self, space_key: str, title: str, body: str, parent_id: str | None = None) -> dict:
        """Neue Seite in Confluence erstellen."""
        try:
            return self.confluence.create_page(space_key, title, body, parent_id=parent_id, type="page")
        except Exception:
            logger.exception("Fehler beim Erstellen der Confluence-Seite")
            raise

    def update_page(self, page_id: str, title: str, body: str) -> dict:
        """Bestehende Seite aktualisieren."""
        try:
            self.confluence.get_page_by_id(page_id, expand="version")
            return self.confluence.update_page(page_id, title, body, minor_edit=False)
        except Exception:
            logger.exception("Fehler beim Aktualisieren der Seite %s", page_id)
            raise

    def get_page_history(self, page_id: str) -> list[dict]:
        """Änderungshistorie einer Seite abrufen."""
        try:
            page = self.confluence.get_page_by_id(page_id, expand="history")
            return [page.get("history", {})]
        except Exception:
            logger.exception("Fehler beim Abrufen der Historie für Seite %s", page_id)
            raise

    @staticmethod
    def _html_to_text(html: str) -> str:
        """HTML-Tags entfernen für Plain-Text."""
        text = re.sub(r"<br\s*/?>", "\n", html)
        text = re.sub(r"</p>|</div>|</li>|</tr>", "\n", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
