from django.urls import path

from .views import (
    book_ticket_page,
    my_tickets_page,
)

urlpatterns = [
    path('book/<int:match_id>/', book_ticket_page, name='book_ticket_page'),
    path('my-tickets/', my_tickets_page, name='my_tickets_page'),
]
