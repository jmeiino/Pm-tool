from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """Erlaubt Zugriff nur fuer Staff-/Admin-Benutzer."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
