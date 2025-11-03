from django.urls import path
from .views import *

urlpatterns = [
    path('new/', CreateNewChat.as_view(), name='create_chat'),
    path('all/', ListUserChats.as_view(), name='cht_list'),
]
