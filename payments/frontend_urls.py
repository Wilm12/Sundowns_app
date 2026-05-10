from django.urls import path

from .views import payment_page, create_membership_payment_page

urlpatterns = [
    path('', payment_page, name='payment_page'),
    path('pay-membership/', create_membership_payment_page, name='create_membership_payment_page'),
]
