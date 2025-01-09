"""
ASGI config for qms_api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

# import os
# import django

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qms_api.settings")
# django.setup()

# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from apps.ticket.routing import websocket_urlpatterns
# from apps.invoice.routing import websocket_urlpatterns
# application = ProtocolTypeRouter(
#     {
#         "http": get_asgi_application(),
#         "websocket": AuthMiddlewareStack(
#             URLRouter(websocket_urlpatterns)
#         ),
#     }
# )

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qms_api.settings")
django.setup()
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.ticket.routing import websocket_urlpatterns as ticket_patterns
from apps.invoice.routing import websocket_urlpatterns as invoice_patterns


# Combine WebSocket URL patterns from all apps
all_websocket_urlpatterns = ticket_patterns + invoice_patterns

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(URLRouter(all_websocket_urlpatterns)),
    }
)
