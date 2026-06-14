from django.urls import path

from . import views

urlpatterns = [
    path('points/tiers/', views.tiers_page, name='tiers_page'),
    path('points/', views.points_dashboard, name='points_dashboard'),
]
