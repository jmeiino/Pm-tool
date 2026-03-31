from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.health import health_check

urlpatterns = [
    path("api/v1/health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    # API
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.projects.urls")),
    path("api/v1/", include("apps.todos.urls")),
    path("api/v1/integrations/", include("apps.integrations.urls")),
    path("api/v1/", include("apps.ai.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/agents/", include("apps.agents.urls")),
    path("api/v1/admin/", include("apps.admin_portal.urls")),
    # API Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
