from django.urls import path
from .views import UserView, UserUpdateView, UserUpdateAvatarView, UsersListAPIView

urlpatterns = [
    path('<int:pk>/', UserView.as_view()),
    path('me/upd/', UserUpdateView.as_view()),
    path('me/la/', UserUpdateAvatarView.as_view()),
    path('gu/', UsersListAPIView.as_view())
]
