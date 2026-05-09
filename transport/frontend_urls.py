from django.urls import path

from .views import (
    transport_list_page,
    book_transport_page,
    my_transport_bookings_page,
)

urlpatterns = [
    path('', transport_list_page, name='transport_list_page'),
    path('book/<int:transport_id>/<int:ticket_id>/', book_transport_page, name='book_transport_page'),
    path('my-bookings/', my_transport_bookings_page, name='my_transport_bookings_page'),
]
