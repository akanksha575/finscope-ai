"""
WebSocket URL routing for Django Channels
"""
from django.urls import re_path
from api.consumers import ResearchStreamConsumer

websocket_urlpatterns = [
    re_path(r"^api/research/stream$", ResearchStreamConsumer.as_asgi()),
]
