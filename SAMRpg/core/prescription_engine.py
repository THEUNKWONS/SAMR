"""
SAMR-17: Generación, firma y validación de receta
Motor para manejar la firma electrónica (criptográfica) de recetas y su posterior validación.
En este MVP, utilizamos HMAC-SHA256 con una clave secreta del sistema como prueba de concepto 
para asegurar la inmutabilidad (Non-Repudiation y Data Integrity).
"""

import hashlib
import hmac
from django.conf import settings

class PrescriptionEngine:
    
    @staticmethod
    def generar_hash_documento(contenido: str) -> str:
        """
        Genera el hash SHA-256 del contenido de la receta para garantizar su integridad.
        """
        if not contenido:
            return ""
        return hashlib.sha256(contenido.encode('utf-8')).hexdigest()

    @staticmethod
    def firmar_receta(medico_id: int, hash_documento: str) -> str:
        """
        Genera una firma digital para el documento utilizando HMAC.
        Simula la aplicación de un certificado digital del médico.
        """
        if not hash_documento:
            return ""
            
        # Simulación de clave privada del médico (combinada con la clave del servidor)
        private_key = f"{settings.SECRET_KEY}_medico_{medico_id}".encode('utf-8')
        
        # Generar firma HMAC-SHA256
        firma = hmac.new(
            private_key, 
            hash_documento.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
        
        return firma

    @staticmethod
    def validar_receta(medico_id: int, contenido: str, firma_proporcionada: str) -> bool:
        """
        Verifica que el contenido no haya sido alterado y que la firma sea válida para el médico.
        """
        if not contenido or not firma_proporcionada:
            return False
            
        hash_actual = PrescriptionEngine.generar_hash_documento(contenido)
        firma_esperada = PrescriptionEngine.firmar_receta(medico_id, hash_actual)
        
        # Comparación segura para mitigar ataques de timing (Timing attacks)
        return hmac.compare_digest(firma_esperada, firma_proporcionada)
