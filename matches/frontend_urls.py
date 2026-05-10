from django.urls import path

from .views import (
    match_list_page,
    match_detail_page,
)

urlpatterns = [
    path('', match_list_page, name='match_list_page'),
    path('<int:match_id>/', match_detail_page, name='match_detail_page'),
]
