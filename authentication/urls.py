from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, MeView, AdminOnlyView, MemberOnlyView
from .views import login_page, logout_page

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('admin-only/', AdminOnlyView.as_view(), name='admin_only'),
    path('member-only/', MemberOnlyView.as_view(), name='member_only'),
    path('login-page/', login_page, name='login_page'),
    path('logout/', logout_page, name='logout_page'),
]