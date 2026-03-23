import logging

from config.celery import app

logger = logging.getLogger(__name__)


@app.task(bind=True)
def check_deadline_warnings(self):
    """Periodischer Task: Fristwarnungen für bald fällige Aufgaben erstellen."""
    from apps.notifications.services import NotificationService

    count = NotificationService.create_deadline_warnings(days_ahead=2)
    logger.info("%d Fristwarnungen erstellt", count)
    return count
