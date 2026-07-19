import hashlib
from django.db.models.signals import post_save
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
