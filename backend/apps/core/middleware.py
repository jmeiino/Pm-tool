from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication

User = get_user_model()

_default_user_cache = None


def _get_default_user():
    global _default_user_cache
    if _default_user_cache is not None:
        try:
            _default_user_cache.refresh_from_db()
            return _default_user_cache
        except User.DoesNotExist:
            _default_user_cache = None

    _default_user_cache, _ = User.objects.get_or_create(
        username="default",
        defaults={
            "first_name": "Max",
            "last_name": "Mustermann",
            "email": "max@beispiel.de",
            "is_active": True,
            "is_staff": True,
        },
    )
    return _default_user_cache


class AutoAuthMiddleware:
    """
    Django-Middleware: setzt request.user auf den Default-User.
    Nur aktiv wenn DEBUG=True (Entwicklungsmodus).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG:
            if not request.user or not request.user.is_authenticated:
                request.user = _get_default_user()
        return self.get_response(request)


class AutoAuthDRF(BaseAuthentication):
    """
    DRF-Authentication-Klasse fuer den Entwicklungsmodus.
    Nur aktiv wenn DEBUG=True.
    """

    def authenticate(self, request):
        if not settings.DEBUG:
            return None
        user = _get_default_user()
        return (user, None)
