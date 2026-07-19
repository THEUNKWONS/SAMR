import base64
import json
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import hashlib

def get_cipher():
    # Derive a 32-byte key from Django's SECRET_KEY
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)

class EncryptedTextField(models.TextField):
    description = "AES-256 encrypted text field"

    def get_prep_value(self, value):
        if value is None or value == '':
            return value
        cipher = get_cipher()
        return cipher.encrypt(str(value).encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        try:
            cipher = get_cipher()
            return cipher.decrypt(value.encode()).decode()
        except Exception:
            return value # Return as is if decryption fails (e.g., old unencrypted data)

class EncryptedJSONField(models.JSONField):
    description = "AES-256 encrypted JSON field"

    def get_prep_value(self, value):
        if value is None:
            return value
        cipher = get_cipher()
        json_str = json.dumps(value)
        return cipher.encrypt(json_str.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            cipher = get_cipher()
            decrypted = cipher.decrypt(value.encode()).decode()
            return json.loads(decrypted)
        except Exception:
            return value
