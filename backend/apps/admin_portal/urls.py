from django.urls import path

from . import views

urlpatterns = [
    # Dashboard
    path("dashboard/", views.AdminDashboardView.as_view(), name="admin-dashboard"),
    # Benutzerverwaltung
    path("users/", views.AdminUserListCreateView.as_view(), name="admin-users-list"),
    path("users/<int:pk>/", views.AdminUserDetailView.as_view(), name="admin-users-detail"),
    # System & Integrationen
    path("system-health/", views.SystemHealthView.as_view(), name="admin-system-health"),
    path("integrations/", views.AdminIntegrationsView.as_view(), name="admin-integrations"),
    path(
        "integrations/<int:pk>/force-sync/",
        views.AdminForceSyncView.as_view(),
        name="admin-force-sync",
    ),
    path("sync-logs/", views.AdminSyncLogsView.as_view(), name="admin-sync-logs"),
    # AI & Agents
    path("ai-stats/", views.AdminAIStatsView.as_view(), name="admin-ai-stats"),
    path("agent-overview/", views.AdminAgentOverviewView.as_view(), name="admin-agent-overview"),
]
