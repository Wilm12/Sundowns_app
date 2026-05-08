from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatchViewSet
from .views import match_list_page

router = DefaultRouter()
router.register('', MatchViewSet, basename='match')

urlpatterns = [
    path('', include(router.urls)),
    path("list-page/", match_list_page, name="match_list_page"),
]
