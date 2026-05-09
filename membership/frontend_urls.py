from django.urls import path

from .views import membership_page

urlpatterns = [
    path('', membership_page, name='membership_page'),
]
