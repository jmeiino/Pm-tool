from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DailyPlanViewSet, PersonalTodoViewSet, WeeklyPlanViewSet

router = DefaultRouter()
router.register(r"todos", PersonalTodoViewSet, basename="todo")
router.register(r"daily-plans", DailyPlanViewSet, basename="daily-plan")
router.register(r"weekly-plans", WeeklyPlanViewSet, basename="weekly-plan")

urlpatterns = [
    path("", include(router.urls)),
]
