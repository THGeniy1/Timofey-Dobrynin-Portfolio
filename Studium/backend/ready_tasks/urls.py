from django.urls import path
from .views import *

urlpatterns = [
    path('cr/', ReadyTaskCreateAPIView.as_view()),
    path('all/', ReadyTaskListAPIView.as_view()),
    path('sold/<int:pk>/', ReadyTaskSoldListAPIView.as_view()),
    path('bought/me/', ReadyTaskBoughtListAPIView.as_view()),
    path('<int:pk>/', ReadyTaskDetailAPIView.as_view()),
    path('rcr/<int:pk>/', ReadyTaskPrepareForRecreateAPIView.as_view()),
    path('hide/<int:id>/', ReadyTaskHideAPIView.as_view())
]
