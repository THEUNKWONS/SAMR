import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'samr_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Paciente, MedicoEspecialista, MedicoAsistente, Especialidad

User = get_user_model()

esp_general, _ = Especialidad.objects.get_or_create(nombre='General')
esp_cardio, _ = Especialidad.objects.get_or_create(nombre='Cardiología')

with open('users_backup.json', 'r') as f:
    users = json.load(f)

for ud in users:
    if User.objects.filter(username=ud['username']).exists():
        continue
    user = User(
        username=ud['username'],
        tipoUsuario=ud['tipoUsuario'],
        first_name=ud['first_name'],
        last_name=ud['last_name'],
        email=ud['email'],
        is_superuser=ud['is_superuser']
    )
    user.password = ud['password']
    user.save()
    
    if ud['tipoUsuario'] == 'PACIENTE':
        Paciente.objects.get_or_create(usuario=user)
    elif ud['tipoUsuario'] == 'MEDICO_ESPECIALISTA':
        MedicoEspecialista.objects.get_or_create(
            usuario=user,
            defaults={'registro_profesional': 'MED-1234', 'especialidad': esp_cardio}
        )
    elif ud['tipoUsuario'] == 'MEDICO_ASISTENTE':
        MedicoAsistente.objects.get_or_create(
            usuario=user,
            defaults={'turno': 'Mañana'}
        )
    
print("Usuarios restaurados.")
