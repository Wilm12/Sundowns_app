from django.urls import path

from .views import (
    book_ticket_page,
    my_tickets_page,
    verify_ticket_page,
    transport_prompt_page,
)

urlpatterns = [
<<<<<<< HEAD
    path('book/<int:match_id>/', book_ticket_page, name='book_ticket_page'),
    path('my-tickets/', my_tickets_page, name='my_tickets_page'),
    path("verify/", verify_ticket_page, name="verify_ticket_page"),
    path("transport-prompt/<int:ticket_id>/", transport_prompt_page, name="transport_prompt_page"),
]
=======
    path(
        "book/<int:match_id>/",
        book_ticket_page,
        name="book_ticket_page"
    ),

    path(
        "my-tickets/",
        my_tickets_page,
        name="my_tickets_page"
    ),

   path(
    "<int:ticket_id>/transport-prompt/",
    transport_prompt_page,
    name="transport_prompt_page"
    ),

    path(
        "verify/",
        verify_ticket_page,
        name="verify_ticket_page"
    ),
]
>>>>>>> feature/testing-environment
