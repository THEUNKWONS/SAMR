from django.db import models
from django.contrib.auth.models import AbstractUser
from core.fields import EncryptedTextField, EncryptedJSONField
# Usaremos encrypt() directamente en los modelos.

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
    # Cifrado AES-256 Real para datos médicos sensibles
    historialClinicoBasico = EncryptedTextField(blank=True, null=True)
    alergias = EncryptedTextField(blank=True, null=True)

class Familiar(models.Model):
    ESTADOS_SOLICITUD = [
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADO', 'Aceptado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_familiar')
    paciente_asociado = models.ForeignKey(Paciente, on_delete=models.SET_NULL, null=True, blank=True)
    relacionConPaciente = models.CharField(max_length=50)
    estado_solicitud = models.CharField(max_length=20, choices=ESTADOS_SOLICITUD, default='PENDIENTE')

class MedicoEspecialista(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_especialista')
    especialidad = models.CharField(max_length=100)
    registro_profesional = models.CharField(max_length=50)
    firmaElectronica = models.TextField(blank=True, null=True)
    # SAMR-15: Campos para matching inteligente
    disponible = models.BooleanField(default=True)
    carga_trabajo = models.IntegerField(default=0, help_text="Cantidad de pacientes activos asignados")

class MedicoAsistente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_asistente')
    turno = models.CharField(max_length=50)
    # SAMR-15: Campos para matching inteligente
    disponible = models.BooleanField(default=True)
    carga_trabajo = models.IntegerField(default=0, help_text="Cantidad de pacientes activos asignados")

class EntidadCertificadora(models.Model):
    llavePublica = models.TextField()
    estadoCertificado = models.CharField(max_length=50)

class Telemetria(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    # Cifrado AES-256 Real para telemetría en reposo
    datosTelemetria = EncryptedJSONField(blank=True, null=True)
    umbralAnomalia = models.CharField(max_length=50)
    estadoProcesamiento = models.CharField(max_length=50, default='Pendiente')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Telemetría de {self.paciente.usuario.first_name} - {self.timestamp}"

class AuditLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=255)
    cryptographic_hash = models.CharField(max_length=64, help_text="SHA-256 hash for WORM compliance")
    
    def __str__(self):
        return f"AUDIT [{self.timestamp}] {self.action} on {self.model_name}"

class TriageLog(models.Model):
    ESTADOS_ASIGNACION = [
        ('PENDIENTE', 'Pendiente'),
        ('ATENDIDO', 'Atendido'),
    ]
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='triajes')
    sintomas_reportados = models.TextField()
    nivel_alerta = models.CharField(max_length=20)
    respuesta_ia = models.TextField()
    resumen_medico = models.TextField()
    estado_asignacion = models.CharField(max_length=20, choices=ESTADOS_ASIGNACION, default='PENDIENTE')
    # SAMR-15: Médico asignado por el matching inteligente
    medico_asignado = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='triajes_asignados')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Triaje {self.nivel_alerta} - {self.paciente.usuario.username} - {self.timestamp}"

class Receta(models.Model):
    triaje = models.OneToOneField(TriageLog, on_delete=models.CASCADE, related_name='receta')
    # Cifrado AES-256 para proteger el diagnóstico y medicamentos
    contenido = EncryptedTextField(blank=True, null=True)
    firmada = models.BooleanField(default=False)
    
    # SAMR-17: Campos para firma electrónica y validación
    firma_digital = models.TextField(blank=True, null=True, help_text="Firma criptográfica del médico")
    hash_documento = models.CharField(max_length=64, blank=True, null=True, help_text="SHA-256 del contenido original")
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receta para {self.triaje.paciente.usuario.first_name} - Firmada: {self.firmada}"


# --- SAMR-13: Modelos para Triaje RAG ---

class MedicalProtocol(models.Model):
    """Protocolo medico almacenado para consulta RAG durante el triaje automatizado."""
    CATEGORIAS = [
        ('Cardiovascular', 'Cardiovascular'),
        ('Respiratorio', 'Respiratorio'),
        ('Neurologico', 'Neurologico'),
        ('Alergias', 'Alergias'),
        ('Gastrointestinal', 'Gastrointestinal'),
        ('Traumatologia', 'Traumatologia'),
        ('Infeccioso', 'Infeccioso'),
        ('Salud Mental', 'Salud Mental'),
        ('Pediatrico', 'Pediatrico'),
        ('General', 'General'),
    ]
    NIVELES = [
        ('critico', 'Critico'),
        ('medio', 'Medio'),
        ('bajo', 'Bajo'),
    ]
    protocol_id = models.CharField(max_length=20, unique=True)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS)
    titulo = models.CharField(max_length=200)
    contenido = models.TextField(help_text="Guia clinica completa del protocolo")
    nivel_sugerido = models.CharField(max_length=10, choices=NIVELES)
    palabras_clave = models.TextField(help_text="Palabras clave separadas por coma")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.protocol_id}] {self.titulo} ({self.categoria})"

    class Meta:
        ordering = ['categoria', 'protocol_id']


class RAGQueryLog(models.Model):
    """Registro de consultas RAG realizadas durante el triaje para trazabilidad."""
    triaje = models.ForeignKey(TriageLog, on_delete=models.CASCADE, related_name='rag_queries', null=True, blank=True)
    sintomas_query = models.TextField(help_text="Sintomas enviados al motor RAG")
    protocolos_recuperados = models.TextField(help_text="IDs de protocolos recuperados")
    nivel_sugerido_rag = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RAG Query [{self.nivel_sugerido_rag}] - {self.timestamp}"

