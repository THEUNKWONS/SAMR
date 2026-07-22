import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'samr_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from core.views import aceptar_triaje
from core.models import TriageLog, Paciente, Especialidad

User = get_user_model()
user = User.objects.filter(tipoUsuario='MEDICO_ESPECIALISTA').first()
triaje = TriageLog.objects.filter(estado_asignacion='PENDIENTE').first()

if not triaje:
    print("No pending triaje to test")
else:
    factory = RequestFactory()
    request = factory.post(f'/api/triaje/{triaje.id}/aceptar/')
    request.user = user
    response = aceptar_triaje(request, triaje.id)
    print("Response status:", response.status_code)
    print("Response content:", response.content)
