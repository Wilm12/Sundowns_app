from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('health/', health_check),

    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/users/', include('users.urls')),
    path('api/branches/', include('branches.urls')),
    path('api/memberships/', include('membership.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/tickets/', include('ticketing.urls')),
    path('api/matches/', include('matches.urls')),
    path('api/transport/', include('transport.urls')),
]