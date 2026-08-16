from django.urls import path
from .views import analytics_dashboard_view, analytics_snapshot_dashboard

urlpatterns = [
    path('', analytics_dashboard_view, name='analytics_dashboard'),
    path('snapshots/', analytics_snapshot_dashboard, name='analytics_snapshot_dashboard'),
]
