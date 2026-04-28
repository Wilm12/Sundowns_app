from django.urls import path
from .views import (
    MembershipListCreateView,
    MembershipDetailView,
    MyMembershipsView,
)

urlpatterns = [
    path('', MembershipListCreateView.as_view(), name='membership_list_create'),
    path('me/', MyMembershipsView.as_view(), name='my_memberships'),
    path('<int:pk>/', MembershipDetailView.as_view(), name='membership_detail'),
]
