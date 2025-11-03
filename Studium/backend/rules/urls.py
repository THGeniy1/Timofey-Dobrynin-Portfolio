from django.urls import path
from .views import *

urlpatterns = [
    path('get_all/', RulesListAPIView.as_view()),
]
