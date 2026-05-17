from django.urls import path

from .views import my_branch_page, branch_detail_page

urlpatterns = [
    path('', my_branch_page, name='my_branch_page'),
    path('<int:branch_id>/', branch_detail_page, name='branch_detail_page'),
]
