from django.urls import path
from .views import (
    TransportListCreateView,
    TransportDetailView,
    TransportBookingListCreateView,
    TransportBookingDetailView,
    MyTransportBookingsView,
    TransportSettlementListCreateView,
    TransportSettlementDetailView,
)

urlpatterns = [
    path('', TransportListCreateView.as_view(), name='transport_list_create'),
    path('<int:pk>/', TransportDetailView.as_view(), name='transport_detail'),

    path('bookings/', TransportBookingListCreateView.as_view(), name='transport_booking_list_create'),
    path('bookings/me/', MyTransportBookingsView.as_view(), name='my_transport_bookings'),
    path('bookings/<int:pk>/', TransportBookingDetailView.as_view(), name='transport_booking_detail'),

    path('settlements/', TransportSettlementListCreateView.as_view(), name='transport_settlement_list_create'),
    path('settlements/<int:pk>/', TransportSettlementDetailView.as_view(), name='transport_settlement_detail'),
]
