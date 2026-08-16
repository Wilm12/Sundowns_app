from django.contrib import admin
from django.urls import path, include
from common.views import user_settings_view
from django.http import JsonResponse
from matches.views import match_list_page, match_detail_page
from django.urls import include, path
from branches.views_admin_dashboard import branch_admin_dashboard_view
from branches.views_branch_performance import branch_performance_view

from common.views import (
    home_view,
    dashboard_view,
    admin_dashboard_view,
    user_settings_view,
    change_password_view,
)

from common.views import home_view, dashboard_view
from matches.views import match_list_page, match_detail_page

def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", include("django_prometheus.urls")),
    path('', home_view, name='home'),
    path('health/', health_check),
    path("common/", include("common.urls")),
    path('admin/', admin.site.urls),
    path("", include("django_prometheus.urls")),

    # Frontend/template routes
    path('dashboard/', dashboard_view, name='dashboard'),
    path('branch-admin/', branch_admin_dashboard_view, name='branch_admin_dashboard'),
    path('branch-admin/<int:branch_id>/', branch_admin_dashboard_view, name='branch_admin_dashboard_branch'),
    path('branch-admin/<int:branch_id>/performance/', branch_performance_view, name='branch_performance'),
    path('matches/', include('matches.frontend_urls')),
    path('tickets/', include('ticketing.frontend_urls')),
    path('payments/', include('payments.frontend_urls')),
    path('transport/', include('transport.frontend_urls')),
    path('membership/', include('membership.frontend_urls')),
    path('branches/', include('branches.frontend_urls')),
    path('rewards/', include('rewards.urls')),
    path('notifications/', include('notifications.urls')),
    path('analytics/', include('analytics.urls')),
    path('', include('points.urls')),
    path("settings/", user_settings_view, name="user_settings"),
    path("settings/change-password/", change_password_view, name="change_password"),
    path('admin-dashboard/', admin_dashboard_view, name='admin_dashboard'),

    # API routes
    path('api/auth/', include('authentication.urls')),
    path('api/users/', include('users.urls')),
    path('api/branches/', include('branches.urls')),
    path('api/memberships/', include('membership.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/tickets/', include('ticketing.urls')),
    path('api/matches/', include('matches.urls')),
    path('api/transport/', include('transport.urls')),
]