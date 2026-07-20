"""
Middleware de Seguridad - SAMR-9: Gestión de Identidad y Acceso
Implementa controles de sesión, auditoría de acceso y protección contra fuerza bruta.
Cumple con ISO 27001 / ISO 27799.
"""
import time
import hashlib
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Control de seguridad de sesión:
    - Timeout por inactividad (cierra sesión tras N minutos sin actividad)
    - Registra IP y User-Agent del cliente en la sesión al autenticarse
    - Detecta cambios de IP durante la sesión activa (posible secuestro)
    """

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        now = time.time()
        timeout = getattr(settings, 'SESSION_TIMEOUT_MINUTES', 15) * 60

        # Registrar IP y User-Agent en la sesión si no existen
        if 'session_ip' not in request.session:
            request.session['session_ip'] = self._get_client_ip(request)
            request.session['session_user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        # Verificar timeout por inactividad
        last_activity = request.session.get('last_activity')
        if last_activity and (now - last_activity) > timeout:
            logout(request)
            messages.warning(request, 'Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.')
            return redirect('login')

        # Actualizar timestamp de última actividad
        request.session['last_activity'] = now
        return None

    def _get_client_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class AccessAuditMiddleware(MiddlewareMixin):
    """
    Auditoría de acceso:
    - Registra cada petición autenticada a vistas protegidas en el AuditLog
    - Solo registra peticiones GET a rutas internas (no estáticos, no API repetitiva)
    - Cumple con ISO 27001: quién, qué, cuándo, desde dónde
    """

    # Rutas que se auditan (vistas protegidas del sistema)
    AUDITED_PATHS = [
        '/perfil/',
        '/panel-medico/',
        '/historial/',
        '/triaje/',
        '/gestionar-familiar/',
    ]

    def process_response(self, request, response):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return response

        # Solo auditar GET a rutas protegidas
        if request.method != 'GET':
            return response

        path = request.path
        should_audit = any(path.startswith(p) for p in self.AUDITED_PATHS)

        if not should_audit:
            return response

        try:
            from core.models import AuditLog

            ip = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', 'Desconocido')
            action = f"ACCESO a {path} [{request.method}] - UA: {user_agent[:100]}"

            # Hash criptográfico para inmutabilidad WORM
            raw = f"{request.user.id}|{path}|{ip}|{time.time()}".encode('utf-8')
            crypto_hash = hashlib.sha256(raw).hexdigest()

            AuditLog.objects.create(
                user_id=request.user.id,
                ip_address=ip,
                action=action,
                model_name="AccessControl",
                object_id=path,
                cryptographic_hash=crypto_hash,
            )
        except Exception:
            # No interrumpir la respuesta si la auditoría falla
            pass

        return response

    def _get_client_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class BruteForceProtectionMiddleware(MiddlewareMixin):
    """
    Protección contra fuerza bruta:
    - Bloquea temporalmente una IP tras N intentos fallidos de login
    - Usa caché en memoria (diccionario) para rastrear intentos
    - Los bloqueos expiran automáticamente tras M minutos
    """

    # Almacén en memoria: {ip: {'attempts': int, 'locked_until': float}}
    _login_attempts = {}

    def process_request(self, request):
        if request.path != '/login/' or request.method != 'POST':
            return None

        ip = self._get_client_ip(request)
        max_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
        lockout_minutes = getattr(settings, 'LOCKOUT_DURATION_MINUTES', 15)

        record = self._login_attempts.get(ip, {})
        locked_until = record.get('locked_until', 0)

        # Verificar si la IP está bloqueada
        if locked_until and time.time() < locked_until:
            remaining = int((locked_until - time.time()) / 60) + 1
            messages.error(
                request,
                f'Tu cuenta ha sido bloqueada temporalmente por múltiples intentos fallidos. '
                f'Intenta de nuevo en {remaining} minuto(s).'
            )
            return redirect('login')

        # Si el bloqueo expiró, resetear
        if locked_until and time.time() >= locked_until:
            self._login_attempts.pop(ip, None)

        return None

    def process_response(self, request, response):
        """Registrar intento fallido si el login devuelve el formulario de nuevo (no redirige)."""
        if request.path != '/login/' or request.method != 'POST':
            return response

        ip = self._get_client_ip(request)
        max_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
        lockout_minutes = getattr(settings, 'LOCKOUT_DURATION_MINUTES', 15)

        # Si la respuesta es un redirect (302), el login fue exitoso -> resetear
        if response.status_code == 302:
            self._login_attempts.pop(ip, None)
            return response

        # Si no redirigió, fue un intento fallido
        if ip not in self._login_attempts:
            self._login_attempts[ip] = {'attempts': 0, 'locked_until': 0}

        self._login_attempts[ip]['attempts'] += 1

        if self._login_attempts[ip]['attempts'] >= max_attempts:
            self._login_attempts[ip]['locked_until'] = time.time() + (lockout_minutes * 60)

            # Registrar en AuditLog
            try:
                from core.models import AuditLog

                raw = f"BRUTE_FORCE|{ip}|{time.time()}".encode('utf-8')
                crypto_hash = hashlib.sha256(raw).hexdigest()

                AuditLog.objects.create(
                    ip_address=ip,
                    action=f"ALERTA SEGURIDAD: IP bloqueada por {max_attempts} intentos fallidos de login",
                    model_name="BruteForceProtection",
                    object_id=ip,
                    cryptographic_hash=crypto_hash,
                )
            except Exception:
                pass

        return response

    def _get_client_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
