from django.db import models
from django.contrib.auth.models import AbstractUser

# Simulación de cifrado AES-256 para el prototipo
class EncryptedTextField(models.TextField):
    description = "A simulated AES-256 encrypted text field"
    
    def get_prep_value(self, value):
        if value is None:
            return value
        return f"[CIPHERTEXT_AES256_GCM] {value}"
        
class EncryptedJSONField(models.JSONField):
    description = "A simulated AES-256 encrypted JSON field"
    
    def get_prep_value(self, value):
        if value is None:
            return value
        return f"[CIPHERTEXT_AES256_GCM] {value}"

class Usuario(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('PACIENTE', 'Paciente'),
        ('FAMILIAR', 'Familiar'),
        ('MEDICO_ESPECIALISTA', 'Médico Especialista'),
        ('MEDICO_ASISTENTE', 'Médico Asistente'),
        ('AUDITOR_DPO', 'Auditor DPO'),
    ]
    tipoUsuario = models.CharField(max_length=30, choices=TIPO_USUARIO_CHOICES)
    
    # Datos exhaustivos
    dni = models.CharField(max_length=20, unique=True, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=20, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], null=True, blank=True)
    telefono_principal = models.CharField(max_length=20, null=True, blank=True)
    telefono_emergencia = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.TextField(null=True, blank=True)
    
    acepto_terminos_lopdp = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.tipoUsuario})"

class Paciente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_paciente')
    # Cifrado AES-256 simulado para datos médicos sensibles
    historialClinicoBasico = EncryptedTextField(blank=True, null=True)
    alergias = EncryptedTextField(blank=True, null=True)

class Familiar(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_familiar')
    paciente_asociado = models.ForeignKey(Paciente, on_delete=models.SET_NULL, null=True, blank=True)
    relacionConPaciente = models.CharField(max_length=50)

class MedicoEspecialista(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_especialista')
    especialidad = models.CharField(max_length=100)
    registro_profesional = models.CharField(max_length=50)
    firmaElectronica = models.TextField(blank=True, null=True)

class MedicoAsistente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_asistente')
    turno = models.CharField(max_length=50)

class EntidadCertificadora(models.Model):
    llavePublica = models.TextField()
    estadoCertificado = models.CharField(max_length=50)

class Telemetria(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    # Cifrado AES-256 simulado para telemetría en reposo
    datosTelemetria = EncryptedJSONField(blank=True, null=True)
    umbralAnomalia = models.CharField(max_length=50)
    estadoProcesamiento = models.CharField(max_length=50, default='Pendiente')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Telemetría de {self.paciente.usuario.first_name} - {self.timestamp}"
