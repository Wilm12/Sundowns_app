from django.urls import path
from .views import (
    reward_list_page,
    reward_detail_page,
    redeem_reward_view,
    my_redemptions_page,
)

urlpatterns = [
    path('', reward_list_page, name='reward_list_page'),
    path('<int:reward_id>/', reward_detail_page, name='reward_detail_page'),
    path('<int:reward_id>/redeem/', redeem_reward_view, name='redeem_reward'),
    path('my-redemptions/', my_redemptions_page, name='my_redemptions_page'),
]

