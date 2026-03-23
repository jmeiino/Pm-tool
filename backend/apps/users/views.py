from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import User
from .serializers import UserSerializer


class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Benutzerprofil anzeigen und bearbeiten."""

    serializer_class = UserSerializer
    queryset = User.objects.all()

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        """Aktuellen Benutzer abrufen oder aktualisieren."""
        if request.method == "PATCH":
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(self.get_serializer(request.user).data)
