from django.urls import path
from .views import *

urlpatterns = [
    path('cr/', OrderTaskCreateAPIView.as_view()),
    path('all/', OrderTaskListAPIView.as_view()),
    # path('sold/<int:pk>/', ReadyTaskSoldListAPIView.as_view()),
    # path('bought/me/', ReadyTaskBoughtListAPIView.as_view()),
    path('<int:pk>/', OrderTaskDetailAPIView.as_view()),
    # path('rcr/<int:pk>/', ReadyTaskPrepareForRecreateAPIView.as_view()),
    # path('hide/<int:id>/', ReadyTaskHideAPIView.as_view())
]
