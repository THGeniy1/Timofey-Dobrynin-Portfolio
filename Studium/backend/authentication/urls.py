from django.urls import path
from .views import RegistrationOrTokenView, CustomTokenRefreshView, LogoutView, MeView, PasswordResetAPIView

urlpatterns = [
    path('login/', RegistrationOrTokenView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('reset_password/', PasswordResetAPIView.as_view(), name='reset_password'),
    path('me/', MeView.as_view(), name='user_detail'),
]
