import logging

from config.celery import app

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def poll_jira_updates(self, integration_id: int):
    """Periodischer Task: Neue Änderungen aus Jira abrufen.

    Wird vom Celery-Beat-Scheduler oder manuell über die API ausgelöst.
    """
    # TODO: IntegrationConfig laden und Credentials entschlüsseln
    # TODO: JiraSyncService instanziieren
    # TODO: sync_inbound() aufrufen
    # TODO: last_synced_at und sync_status aktualisieren
    # TODO: Bei Fehler: Retry mit exponentiellem Backoff
    # TODO: Benachrichtigung bei Fehlern senden
    logger.info("poll_jira_updates für Integration %s gestartet", integration_id)
    raise NotImplementedError


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_project_to_jira(self, integration_id: int, project_id: int):
    """Einzelnes Projekt nach Jira synchronisieren.

    Wird ausgelöst, wenn lokale Änderungen an einem Projekt vorgenommen werden.
    """
    # TODO: IntegrationConfig und Project laden
    # TODO: JiraSyncService instanziieren
    # TODO: sync_outbound() für das spezifische Projekt aufrufen
    # TODO: Konflikterkennung durchführen
    # TODO: Bei Konflikten: Benachrichtigung an den Benutzer
    logger.info(
        "sync_project_to_jira für Integration %s, Projekt %s gestartet",
        integration_id,
        project_id,
    )
    raise NotImplementedError
