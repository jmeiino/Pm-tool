from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AIViewSet

router = DefaultRouter()
router.register(r"ai", AIViewSet, basename="ai")

urlpatterns = [
    path("", include(router.urls)),
]
