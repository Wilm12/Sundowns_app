from django.urls import path
from .views import PaymentListCreateView, PaymentDetailView, MyPaymentsView

urlpatterns = [
    path('', PaymentListCreateView.as_view(), name='payment_list_create'),
    path('me/', MyPaymentsView.as_view(), name='my_payments'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
]
