from django.urls import path
from .views import TicketListCreateView, TicketDetailView, MyTicketsView

urlpatterns = [
    path('', TicketListCreateView.as_view(), name='ticket_list_create'),
    path('me/', MyTicketsView.as_view(), name='my_tickets'),
    path('<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
]
