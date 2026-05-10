from django.contrib import admin
from django.urls import path, include
from common.views import user_settings_view
from django.http import JsonResponse
from matches.views import match_list_page, match_detail_page

from common.views import (
    home_view,
    dashboard_view,
    admin_dashboard_view,
)

from common.views import home_view, dashboard_view
from matches.views import match_list_page, match_detail_page

def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('', home_view, name='home'),
    path('health/', health_check),

    path('admin/', admin.site.urls),

    # Frontend/template routes
    path('dashboard/', dashboard_view, name='dashboard'),
    path('matches/', include('matches.frontend_urls')),
    path('tickets/', include('ticketing.frontend_urls')),
    path('payments/', include('payments.frontend_urls')),
    path('transport/', include('transport.frontend_urls')),
    path('membership/', include('membership.frontend_urls')),
    path('branches/', include('branches.frontend_urls')),
    path("settings/", user_settings_view, name="user_settings"),
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