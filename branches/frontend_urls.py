from django.urls import path

from .views import branch_list_page, branch_detail_page

urlpatterns = [
    path('', branch_list_page, name='branch_list_page'),
    path('<int:branch_id>/', branch_detail_page, name='branch_detail_page'),
]
