from django.urls import path

from .views import (
    TicketListCreateView,
    TicketDetailView,
    MyTicketsView,
    TicketVerifyView,
)

urlpatterns = [
    path('', TicketListCreateView.as_view(), name='ticket_list_create'),
    path('me/', MyTicketsView.as_view(), name='my_tickets'),
    path('verify/', TicketVerifyView.as_view(), name='ticket_verify'),
    path('<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
]
    