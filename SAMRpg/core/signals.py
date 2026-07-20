import hashlib
import time
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .models import Paciente, Telemetria, AuditLog
import json
from django.core.serializers.json import DjangoJSONEncoder

def create_audit_log(sender, instance, created, **kwargs):
    action = "CREATED" if created else "UPDATED"
    model_name = sender.__name__
    object_id = str(instance.id)
    
    # Simple hash of the action to simulate cryptographic WORM immutability
    raw_data = f"{action}|{model_name}|{object_id}|{instance.__dict__.get('timestamp', '')}"
    crypto_hash = hashlib.sha256(raw_data.encode()).hexdigest()
    
    AuditLog.objects.create(
        action=action,
        model_name=model_name,
        object_id=object_id,
        cryptographic_hash=crypto_hash
    )

@receiver(post_save, sender=Paciente)
def audit_paciente(sender, instance, created, **kwargs):
    create_audit_log(sender, instance, created, **kwargs)

@receiver(post_save, sender=Telemetria)
def audit_telemetria(sender, instance, created, **kwargs):
    create_audit_log(sender, instance, created, **kwargs)


# --- Signals de Gestión de Identidad y Acceso (SAMR-9) ---

def _get_client_ip(request):
    """Extrae la IP real del cliente considerando proxies."""
    if request is None:
        return '0.0.0.0'
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


@receiver(user_logged_in)
def audit_user_logged_in(sender, request, user, **kwargs):
    """Registra cada inicio de sesión exitoso en el AuditLog."""
    try:
        ip = _get_client_ip(request)
        raw = f"SIGNAL_LOGIN|{user.id}|{ip}|{time.time()}".encode('utf-8')
        crypto_hash = hashlib.sha256(raw).hexdigest()
        AuditLog.objects.create(
            user_id=user.id,
            ip_address=ip,
            action=f"SESIÓN INICIADA (signal): {user.username} ({user.tipoUsuario})",
            model_name="SessionManagement",
            object_id=str(user.id),
            cryptographic_hash=crypto_hash,
        )
    except Exception:
        pass


@receiver(user_logged_out)
def audit_user_logged_out(sender, request, user, **kwargs):
    """Registra cada cierre de sesión en el AuditLog."""
    try:
        if user is None:
            return
        ip = _get_client_ip(request)
        raw = f"SIGNAL_LOGOUT|{user.id}|{ip}|{time.time()}".encode('utf-8')
        crypto_hash = hashlib.sha256(raw).hexdigest()
        AuditLog.objects.create(
            user_id=user.id,
            ip_address=ip,
            action=f"SESIÓN CERRADA (signal): {user.username}",
            model_name="SessionManagement",
            object_id=str(user.id),
            cryptographic_hash=crypto_hash,
        )
    except Exception:
        pass


@receiver(user_login_failed)
def audit_user_login_failed(sender, credentials, request, **kwargs):
    """Registra cada intento de login fallido en el AuditLog."""
    try:
        ip = _get_client_ip(request)
        username = credentials.get('username', 'desconocido')
        raw = f"SIGNAL_LOGIN_FAILED|{username}|{ip}|{time.time()}".encode('utf-8')
        crypto_hash = hashlib.sha256(raw).hexdigest()
        AuditLog.objects.create(
            ip_address=ip,
            action=f"LOGIN FALLIDO (signal): intento con usuario '{username}' desde IP {ip}",
            model_name="SessionManagement",
            object_id=username,
            cryptographic_hash=crypto_hash,
        )
    except Exception:
        pass

