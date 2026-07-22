from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/dashboard/$', consumers.MedicoDashboardConsumer.as_asgi()),
    re_path(r'ws/paciente/$', consumers.PacienteConsumer.as_asgi()),
    re_path(r'ws/telemetria/$', consumers.IoTTelemetriaConsumer.as_asgi()),
]
