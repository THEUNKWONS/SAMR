import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'samr_project.settings')
django.setup()

from core.models import Usuario, MedicoEspecialista

# Crear o actualizar el usuario doctor
email = "doctor@samria.com"
password = "Password123"

try:
    user = Usuario.objects.get(username=email)
    print("El doctor ya existe.")
except Usuario.DoesNotExist:
    user = Usuario.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name="Dr. Gregory",
        last_name="House",
        dni="0987654321",
        tipoUsuario="MEDICO_ESPECIALISTA",
        acepto_terminos_lopdp=True
    )
    
    MedicoEspecialista.objects.create(
        usuario=user,
        especialidad="Medicina Interna",
        registro_profesional="MED-12345"
    )
    print("¡Doctor creado exitosamente!")

print(f"Correo: {email}")
print(f"Contraseña: {password}")
