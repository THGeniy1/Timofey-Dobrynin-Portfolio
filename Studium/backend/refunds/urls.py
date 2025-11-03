from django.urls import path
from .views import RefundCreateView, RefundProcessView

urlpatterns = [
    path('cr/', RefundCreateView.as_view(), name='refund-create'),
    path('process/<int:refund_id>/', RefundProcessView.as_view(), name='refund-process'),
]