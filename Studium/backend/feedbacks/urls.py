from django.urls import path
from .views import *

urlpatterns = [
    path('cr/', FeedbackCreateAPIView.as_view(), name='feedback_create'),
    path('usr/<int:pk>/', UserFeedbacksAPIView.as_view(), name='feedback_user'),
    path('rt/<int:pk>/', ReadyTaskFeedbacksAPIView.as_view(), name='feedback_task'),
]
