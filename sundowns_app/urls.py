from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/users/', include('users.urls')),
    path('api/branches/', include('branches.urls')),
    path('api/memberships/', include('membership.urls')),
    path('api/payments/', include('payments.urls')),
    

]
