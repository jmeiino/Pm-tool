from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

User = get_user_model()


# ─── Custom Token Serializer (gibt User-Daten mit zurueck) ───────────────────


class CustomTokenObtainSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Ungueltige Anmeldedaten."}
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                {"detail": "Ungueltige Anmeldedaten."}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"detail": "Dieses Konto ist deaktiviert."}
            )

        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_active": user.is_active,
                "timezone": user.timezone,
                "daily_capacity_hours": float(user.daily_capacity_hours),
            },
        }


class LoginView(APIView):
    """Login-Endpoint: gibt JWT-Token + User-Daten zurueck."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomTokenObtainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class LogoutView(APIView):
    """Logout: Blacklisted den Refresh-Token."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass
        return Response({"detail": "Erfolgreich abgemeldet."})


class RefreshView(TokenRefreshView):
    """Token-Refresh Endpoint."""

    pass


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Aktuelles Passwort ist falsch.")
        return value


class ChangePasswordView(APIView):
    """Passwort aendern fuer eingeloggte Benutzer."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])

        return Response({"detail": "Passwort erfolgreich geaendert."})
