from django.urls import re_path
from .consumers import *

websocket_urlpatterns = [
    re_path(r"ws/auth/$", AuthConsumer.as_asgi()),
    re_path(r"ws/screener/$", ScreenerConsumer.as_asgi()),
    re_path(r"ws/screenshot/$", ScreenshotConsumer.as_asgi()),
]
