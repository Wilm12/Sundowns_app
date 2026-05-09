from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

from common.views import home_view, dashboard_view
from matches.views import match_list_page


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('', home_view, name='home'),
    path('health/', health_check),

    path('admin/', admin.site.urls),

    # Frontend/template routes
    path('dashboard/', dashboard_view, name='dashboard'),
    path('matches/', match_list_page, name='match_list_page'),
    path('tickets/', include('ticketing.frontend_urls')),

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