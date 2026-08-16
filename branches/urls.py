"""URL configuration for branch API endpoints."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import BranchViewSet, supporter_verification_view
from .views_dashboard import branch_dashboard_view
from .views_operations import match_operations_console

router = DefaultRouter()
router.register('', BranchViewSet, basename='branch')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:branch_id>/dashboard/', branch_dashboard_view, name='branch_dashboard'),
    path('<int:branch_id>/committee/', views.committee_management_view, name='branch_committee'),
    path('<int:branch_id>/supporters/<int:supporter_id>/verify/', supporter_verification_view, name='branch_supporter_verification'),
    path('<int:branch_id>/matches/<int:match_id>/operations/', match_operations_console, name='match_operations_console'),
    path('<int:branch_id>/matches/manage/', views.match_management_view, name='branch_matches_manage'),
    path('<int:branch_id>/matches/<int:match_id>/edit/', views.match_edit_view, name='branch_match_edit'),
    path('<int:branch_id>/matches/<int:match_id>/publish/', views.match_publish_view, name='branch_match_publish'),
]

