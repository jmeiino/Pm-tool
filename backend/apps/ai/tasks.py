import logging

from celery import shared_task

from .services import AIService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_prioritize_todos(self, todos: list) -> list:
    """Asynchrone Priorisierung von Aufgaben."""
    try:
        service = AIService()
        return service.prioritize_todos(todos)
    except Exception as exc:
        logger.error("Fehler bei asynchroner Priorisierung: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_summarize_content(self, content: str, content_type: str = "text") -> str:
    """Asynchrone Zusammenfassung von Inhalten."""
    try:
        service = AIService()
        return service.summarize_content(content, content_type)
    except Exception as exc:
        logger.error("Fehler bei asynchroner Zusammenfassung: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_extract_action_items(self, text: str) -> list:
    """Asynchrone Extraktion von Aktionspunkten."""
    try:
        service = AIService()
        return service.extract_action_items(text)
    except Exception as exc:
        logger.error("Fehler bei asynchroner Aktionspunkt-Extraktion: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_suggest_daily_plan(self, todos: list, calendar_events: list, capacity_hours: float) -> dict:
    """Asynchrone Erstellung eines Tagesplans."""
    try:
        service = AIService()
        return service.suggest_daily_plan(todos, calendar_events, capacity_hours)
    except Exception as exc:
        logger.error("Fehler bei asynchroner Tagesplanung: %s", exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def async_analyze_confluence_page(self, page_content: str) -> dict:
    """Asynchrone Analyse einer Confluence-Seite."""
    try:
        service = AIService()
        return service.analyze_confluence_page(page_content)
    except Exception as exc:
        logger.error("Fehler bei asynchroner Confluence-Analyse: %s", exc)
        raise self.retry(exc=exc)
