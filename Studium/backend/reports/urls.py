from django.urls import path
from .views import *

urlpatterns = [
    path('cr/', ReportCreateAPIView.as_view())
]
