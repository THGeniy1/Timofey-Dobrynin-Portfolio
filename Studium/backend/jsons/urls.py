from django.urls import path
from .views import JsonHintAPIView, JsonMainAPIView, RefreshJsonAPIView


urlpatterns = [
    path("hints/<str:file_name>/", JsonHintAPIView.as_view(), name="get_hints"),
    path("main/", JsonMainAPIView.as_view(), name="get_hints"),
    path("refresh/<str:file_name>/", RefreshJsonAPIView.as_view(), name="refresh_hints"),
]