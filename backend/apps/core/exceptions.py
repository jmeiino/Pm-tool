from rest_framework.exceptions import APIException


class SyncConflictError(APIException):
    status_code = 409
    default_detail = "Synchronisationskonflikt: Die Daten wurden in der Zwischenzeit geändert."
    default_code = "sync_conflict"


class IntegrationError(APIException):
    status_code = 502
    default_detail = "Fehler bei der Kommunikation mit dem externen Dienst."
    default_code = "integration_error"


class AIServiceError(APIException):
    status_code = 503
    default_detail = "Der KI-Dienst ist momentan nicht verfügbar."
    default_code = "ai_service_error"
