import os
import django

# Setup Django FIRST before any imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")
django.setup()

# Now import Django and Channels components
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import django_app.routing

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

# WebSocket routing
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            django_app.routing.websocket_urlpatterns
        )
    ),
})