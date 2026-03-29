from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .auth_views import ChangePasswordView, LoginView, LogoutView, RefreshView
from .views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
    # Auth
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/refresh/", RefreshView.as_view(), name="auth-refresh"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
]
