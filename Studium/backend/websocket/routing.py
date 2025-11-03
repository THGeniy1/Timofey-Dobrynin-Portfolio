from django.urls import path
from channels.routing import URLRouter
from notifications.consumers import NotificationConsumer

websocket_urlpatterns = URLRouter([
    path("ws/connect/", NotificationConsumer.as_asgi()),
])
