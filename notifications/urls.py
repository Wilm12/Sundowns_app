from django.urls import path
from .views import notifications_list_view

urlpatterns = [
    path('', notifications_list_view, name='notifications_list'),
]
