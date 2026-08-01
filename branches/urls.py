"""URL configuration for branch API endpoints."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet
from .views_dashboard import branch_dashboard_view

router = DefaultRouter()
router.register('', BranchViewSet, basename='branch')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:branch_id>/dashboard/', branch_dashboard_view, name='branch_dashboard'),
]

