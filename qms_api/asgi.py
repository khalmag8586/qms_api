"""
ASGI config for qms_api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qms_api.settings')

# application = get_asgi_application()
# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.ticket.routing import websocket_urlpatterns
from django.conf import settings


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qms_api.settings")


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ) if settings.ENVIRONMENT == "production" else URLRouter(websocket_urlpatterns)
    }
)