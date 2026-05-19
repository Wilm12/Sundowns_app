"""Common URL configuration.

This module defines shared URL patterns for the common app.
The health check endpoint is typically used by load balancers and deployment
health monitoring systems to verify the application is running.
"""

from django.urls import path
from .views import health_check

urlpatterns = [
    path("health/", health_check, name="health_check"),
]

