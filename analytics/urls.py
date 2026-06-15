from django.urls import path
from .views import analytics_dashboard_view

urlpatterns = [
    path('', analytics_dashboard_view, name='analytics_dashboard'),
]
