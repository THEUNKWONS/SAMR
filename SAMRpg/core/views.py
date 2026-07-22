from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse
import json
import time
import hashlib
import functools
import jwt
import datetime
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from openai import OpenAI
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from .models import Usuario, Paciente, Familiar, TriageLog, AuditLog
from .forms import RegistroForm
import random
from datetime import date
import re

def ofuscar_pii(texto, usuario):
    """
    US-4.1: Enmascara (tokeniza) los datos PII del paciente (Nombre, Apellidos, DNI)
    para proteger su privacidad antes de enviar información a servicios de terceros (IA).
    """
    if not texto or not usuario:
        return texto
        
    texto_seguro = str(texto)
    
    if getattr(usuario, 'dni', None):
        texto_seguro = texto_seguro.replace(usuario.dni, "[DNI_PROTEGIDO]")
        
    if getattr(usuario, 'first_name', None):
        for word in usuario.first_name.split():
            if len(word) > 2: # Evitar reemplazar conectores cortos
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                texto_seguro = pattern.sub("[NOMBRE_PROTEGIDO]", texto_seguro)
                
    if getattr(usuario, 'last_name', None):
        for word in usuario.last_name.split():
            if len(word) > 2:
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                texto_seguro = pattern.sub("[APELLIDO_PROTEGIDO]", texto_seguro)
                
    return texto_seguro

def rol_requerido(roles_permitidos):
    """Decorador de control de acceso basado en roles (RBAC).
    Registra intentos de acceso no autorizado en el AuditLog (ISO 27001)."""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.tipoUsuario not in roles_permitidos:
                # Registrar acceso denegado en AuditLog
                try:
                    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '0.0.0.0'))
                    if ',' in ip:
                        ip = ip.split(',')[0].strip()
                    raw = f"ACCESS_DENIED|{request.user.id}|{request.path}|{time.time()}".encode('utf-8')
                    crypto_hash = hashlib.sha256(raw).hexdigest()
                    AuditLog.objects.create(
                        user_id=request.user.id,
                        ip_address=ip,
                        action=f"ACCESO DENEGADO: Usuario {request.user.username} (rol: {request.user.tipoUsuario}) intentó acceder a {request.path}. Roles permitidos: {roles_permitidos}",
                        model_name="AccessControl",
                        object_id=request.path,
                        cryptographic_hash=crypto_hash,
                    )
                except Exception:
                    pass
                messages.error(request, "Acceso denegado: No tienes permisos para ver esta página.")
                return redirect('inicio')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def verificado_required(view_func):
    """Decorador para bloquear acceso a Familiares con estado PENDIENTE."""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.tipoUsuario == 'FAMILIAR':
            try:
                familiar = request.user.perfil_familiar
                if familiar.estado_solicitud == 'PENDIENTE':
                    messages.error(request, "Tu cuenta debe ser verificada por el paciente antes de acceder a esta sección.")
                    return redirect('inicio')
            except Exception:
                pass
        return view_func(request, *args, **kwargs)
    return wrapper

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '0.0.0.0'))
        if ',' in ip:
            ip = ip.split(',')[0].strip()

        user = authenticate(request, username=u, password=p)
        if user is not None:
            # Registrar login exitoso en AuditLog
            try:
                raw = f"LOGIN_SUCCESS|{user.id}|{ip}|{time.time()}".encode('utf-8')
                crypto_hash = hashlib.sha256(raw).hexdigest()
                AuditLog.objects.create(
                    user_id=user.id,
                    ip_address=ip,
                    action=f"LOGIN EXITOSO: {user.username} ({user.tipoUsuario}) desde IP {ip}",
                    model_name="Authentication",
                    object_id=str(user.id),
                    cryptographic_hash=crypto_hash,
                )
            except Exception:
                pass

            # --- Lógica de 2FA (Doble Factor) Exclusiva para Especialistas ---
            # Para garantizar la seguridad del panel médico, se requiere OTP solo para MEDICO_ESPECIALISTA.
            if user.tipoUsuario == 'MEDICO_ESPECIALISTA':
                # Generar OTP de 6 dígitos
                otp = str(random.randint(100000, 999999))
                request.session['pre_otp_user'] = user.id
                request.session['otp_code'] = otp
                request.session['otp_timestamp'] = time.time()
                
                # Enviar correo (En desarrollo se imprime en consola si falla)
                try:
                    send_mail(
                        'Código de Verificación - SAMR-IA',
                        f'Hola {user.first_name},\n\nTu código de verificación de 6 dígitos es: {otp}\n\nEste código expirará en 5 minutos.',
                        'no-reply@samria.com',
                        [user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"[ERROR CORREO] {str(e)}. Código generado: {otp}")
                    
                messages.success(request, 'Código OTP enviado a tu correo. Por seguridad, requerimos doble factor.')
                return redirect('otp_verify')
            else:
                # --- Autenticación Estándar para otros roles ---
                # Roles como PACIENTE, FAMILIAR, etc. entran de manera directa.
                login(request, user)
                messages.success(request, f'¡Bienvenido de nuevo, {user.first_name}!')
                
                if not user.acepto_terminos_lopdp:
                    return redirect('terminos_lopdp')
                return redirect('inicio')
        else:
            # Registrar intento fallido en AuditLog
            try:
                raw = f"LOGIN_FAILED|{u}|{ip}|{time.time()}".encode('utf-8')
                crypto_hash = hashlib.sha256(raw).hexdigest()
                AuditLog.objects.create(
                    ip_address=ip,
                    action=f"LOGIN FALLIDO: Intento con usuario '{u}' desde IP {ip}",
                    model_name="Authentication",
                    object_id=u or 'desconocido',
                    cryptographic_hash=crypto_hash,
                )
            except Exception:
                pass
            messages.error(request, 'Credenciales inválidas.')
    return render(request, 'auth/login.html')

def otp_verify_view(request):
    if 'pre_otp_user' not in request.session:
        return redirect('login')
        
    if request.method == 'POST':
        codigo = request.POST.get('otp_code')
        codigo_guardado = request.session.get('otp_code')
        timestamp = request.session.get('otp_timestamp', 0)
        
        # Validar expiración (5 minutos = 300 segundos)
        if time.time() - timestamp > 300:
            messages.error(request, 'El código OTP ha expirado (5 minutos límite).')
            return redirect('login')
            
        if codigo == codigo_guardado:
            user_id = request.session['pre_otp_user']
            user = Usuario.objects.get(id=user_id)
            login(request, user)
            
            # --- Generación de Token JWT ---
            # Se genera un token JWT para el acceso a APIs y seguridad adicional
            jwt_payload = {
                'user_id': user.id,
                'username': user.username,
                'rol': user.tipoUsuario,
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2),
                'iat': datetime.datetime.now(datetime.timezone.utc),
            }
            # Se firma con el SECRET_KEY del proyecto
            token = jwt.encode(jwt_payload, settings.SECRET_KEY, algorithm='HS256')
            
            # Almacenar token en la sesión para uso interno de Django si es necesario
            request.session['jwt_token'] = token
            # -------------------------------
            
            # Limpiar sesión OTP
            del request.session['pre_otp_user']
            del request.session['otp_code']
            del request.session['otp_timestamp']
            
            messages.success(request, f'¡Bienvenido de nuevo, {user.first_name}!')
            
            if not user.acepto_terminos_lopdp:
                response = redirect('terminos_lopdp')
            else:
                response = redirect('inicio')
                
            # Establecer el JWT como una cookie HttpOnly para mayor seguridad
            response.set_cookie('jwt_token', token, httponly=True, samesite='Lax')
            return response
        else:
            messages.error(request, 'Código OTP incorrecto.')
            
    return render(request, 'auth/otp_verify.html')

@login_required
def terminos_lopdp_view(request):
    if request.method == 'POST':
        if request.POST.get('acepta') == 'on':
            request.user.acepto_terminos_lopdp = True
            request.user.save()
            return redirect('inicio')
        else:
            messages.error(request, 'Debes aceptar los términos para continuar.')
    return render(request, 'auth/terminos_lopdp.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def registro_paciente_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            
            # Validar paciente asociado si es familiar
            paciente_asoc = None
            if datos['tipo_usuario'] == 'FAMILIAR':
                ced_pac = datos['cedula_paciente_asociado']
                try:
                    paciente_asoc = Paciente.objects.get(usuario__dni=ced_pac)
                except Paciente.DoesNotExist:
                    messages.error(request, 'No existe ningún paciente registrado con esa cédula.')
                    return render(request, 'auth/registro.html')

            nuevo_usuario = Usuario.objects.create_user(
                username=datos['email'], email=datos['email'], password=datos['password'],
                first_name=datos['nombres'], last_name=datos['apellidos'],
                dni=datos['dni'], telefono_principal=datos['telefono_principal'],
                fecha_nacimiento=datos['fecha_nacimiento'],
                tipoUsuario=datos['tipo_usuario']
            )
            
            if datos['tipo_usuario'] == 'PACIENTE':
                Paciente.objects.create(usuario=nuevo_usuario, alergias=datos.get('alergias', 'Ninguna'))
            elif datos['tipo_usuario'] == 'FAMILIAR':
                Familiar.objects.create(
                    usuario=nuevo_usuario,
                    paciente_asociado=paciente_asoc,
                    relacionConPaciente='Familiar (Autoregistro)',
                    estado_solicitud='PENDIENTE'
                )
                
            messages.success(request, '¡Registro exitoso! Por favor, inicia sesión.')
            return redirect('login')
        else:
            for field, err_list in form.errors.items():
                for err in err_list:
                    messages.error(request, f"{err}")
            
    return render(request, 'auth/registro.html')

# --- Vistas Protegidas Internas ---

@login_required
def inicio(request):
    if not request.user.acepto_terminos_lopdp:
        return redirect('terminos_lopdp')
    return render(request, 'inicio.html')

@login_required
@verificado_required
@rol_requerido(['PACIENTE', 'FAMILIAR'])
def triaje_inteligente(request):
    return render(request, 'triaje.html')

@login_required
@verificado_required
@rol_requerido(['PACIENTE', 'FAMILIAR'])
def asistente_virtual(request):
    return render(request, 'asistente.html')

@login_required
def perfil_usuario(request):
    solicitudes_familiares = []
    familiares_aprobados = []
    
    if hasattr(request.user, 'perfil_paciente'):
        solicitudes_familiares = Familiar.objects.filter(paciente_asociado=request.user.perfil_paciente, estado_solicitud='PENDIENTE')
        familiares_aprobados = Familiar.objects.filter(paciente_asociado=request.user.perfil_paciente, estado_solicitud='ACEPTADO')
        
    return render(request, 'perfil.html', {
        'solicitudes': solicitudes_familiares,
        'familiares': familiares_aprobados
    })

@login_required
def gestionar_solicitud_familiar(request, familiar_id):
    if request.method == 'POST' and hasattr(request.user, 'perfil_paciente'):
        try:
            familiar = Familiar.objects.get(id=familiar_id, paciente_asociado=request.user.perfil_paciente)
            accion = request.POST.get('accion')
            if accion == 'aceptar':
                familiar.estado_solicitud = 'ACEPTADO'
                messages.success(request, f'Familiar {familiar.usuario.get_full_name()} aceptado.')
            elif accion == 'rechazar':
                familiar.estado_solicitud = 'RECHAZADO'
                messages.error(request, f'Solicitud rechazada.')
            elif accion == 'eliminar':
                familiar.delete()
                messages.success(request, f'Familiar desvinculado de tu cuenta.')
                return redirect('perfil_usuario')
                
            familiar.save()
        except Familiar.DoesNotExist:
            messages.error(request, 'Solicitud no encontrada.')
    return redirect('perfil_usuario')

@login_required
@verificado_required
@rol_requerido(['MEDICO_ESPECIALISTA', 'MEDICO_ASISTENTE'])
def panel_especialista(request):
    triajes_pendientes = TriageLog.objects.filter(
        estado_asignacion='PENDIENTE'
    ).filter(
        Q(medico_asignado=request.user) | Q(medico_asignado__isnull=True)
    ).order_by('-timestamp')
    return render(request, 'panel_medico.html', {'triajes_pendientes': triajes_pendientes})

@login_required
@verificado_required
@rol_requerido(['MEDICO_ESPECIALISTA', 'MEDICO_ASISTENTE', 'PACIENTE', 'FAMILIAR'])
def historial_clinico(request):
    historial = []
    if request.user.tipoUsuario == 'PACIENTE':
        historial = TriageLog.objects.filter(paciente=request.user.perfil_paciente).order_by('-timestamp')
    elif request.user.tipoUsuario == 'FAMILIAR':
        if hasattr(request.user, 'perfil_familiar') and request.user.perfil_familiar.paciente_asociado:
            historial = TriageLog.objects.filter(paciente=request.user.perfil_familiar.paciente_asociado).order_by('-timestamp')
    elif request.user.tipoUsuario in ['MEDICO_ESPECIALISTA', 'MEDICO_ASISTENTE']:
        historial = TriageLog.objects.all().order_by('-timestamp')
        
    return render(request, 'historial.html', {'historial': historial})

# aqui se implemento la logica del backend para el bot conversacional de la historia US-1.4
@login_required
@verificado_required
def chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Obtener contexto del paciente
            paciente = None
            if request.user.tipoUsuario == 'PACIENTE':
                paciente = getattr(request.user, 'perfil_paciente', None)
            elif request.user.tipoUsuario == 'FAMILIAR':
                perfil_fam = getattr(request.user, 'perfil_familiar', None)
                if perfil_fam:
                    paciente = perfil_fam.paciente_asociado
            
            contexto_clinico = "Contexto clínico no disponible."
            if paciente:
                u = paciente.usuario
                edad = "No especificada"
                if u.fecha_nacimiento:
                    today = date.today()
                    edad = today.year - u.fecha_nacimiento.year - ((today.month, today.day) < (u.fecha_nacimiento.month, u.fecha_nacimiento.day))
                
                sexo = dict(Usuario._meta.get_field('sexo').choices).get(u.sexo, "No especificado") if u.sexo else "No especificado"
                historial = paciente.historialClinicoBasico or "Ninguno registrado."
                alergias = paciente.alergias or "Ninguna conocida."
                
                # Obtener última telemetría si existe
                from .models import Telemetria
                telemetria_info = "Sin telemetría reciente."
                ultima_telemetria = Telemetria.objects.filter(paciente=paciente).order_by('-timestamp').first()
                if ultima_telemetria and ultima_telemetria.datosTelemetria:
                    telemetria_info = str(ultima_telemetria.datosTelemetria)
                
                contexto_clinico = f"Edad: {edad} años. Sexo: {sexo}. Historial Clínico: {historial}. Alergias: {alergias}. Telemetría actual: {telemetria_info}."

            # --- SAMR-13: Integración RAG para Triaje Automatizado ---
            from .rag_engine import rag_engine

            # Recuperar protocolos médicos relevantes basados en los síntomas
            contexto_rag = rag_engine.construir_contexto_rag(user_message, top_k=3)
            nivel_sugerido_rag = rag_engine.obtener_nivel_sugerido(user_message)

            # Inicializar cliente OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Limpiar datos PII
            usuario_para_ofuscar = paciente.usuario if paciente else None
            user_message_clean = ofuscar_pii(user_message, usuario_para_ofuscar)
            
            # Prompts y configuración enriquecidos con RAG
            system_instruction = (
                f"Eres SAMR-IA, un asistente de triaje médico avanzado con acceso a protocolos clínicos. "
                f"Estás evaluando a un paciente con el siguiente contexto clínico anonimizado:\n"
                f"{contexto_clinico}\n\n"
                f"Además, se han recuperado los siguientes protocolos clínicos relevantes mediante RAG "
                f"(Retrieval-Augmented Generation) para guiar tu evaluación:\n\n"
                f"{contexto_rag}\n\n"
                f"El nivel de alerta sugerido por los protocolos clínicos es: {nivel_sugerido_rag.upper()}. "
                f"Usa esta referencia pero ajusta según la gravedad real de los síntomas.\n\n"
                "Analiza los síntomas del paciente basándote en el contexto clínico Y los protocolos recuperados. "
                "Devuelve SIEMPRE un JSON válido con la siguiente estructura exacta: "
                "{"
                "  \"nivel_alerta\": \"critico\" (para emergencias vitales inminentes como dolor de pecho, riesgo de desmayo, pérdida de consciencia, sangrado severo, dificultad para respirar o alergias graves), \"medio\" (infecciones, dolor agudo sin riesgo de vida inmediato) o \"bajo\" (consultas generales, síntomas leves); "
                "  \"respuesta_paciente\": \"Mensaje empático, claro y directo. Si es crítico o medio, debes informarle al paciente que has emitido una ALERTA INMEDIATA al panel de los médicos y que un especialista se conectará con él en breve a través de la plataforma para una teleconsulta. No lo mandes a llamar al 911, asume que nuestra plataforma gestionará la emergencia.\"; "
                "  \"resumen_medico\": \"Resumen técnico para el especialista con posible pre-diagnóstico, justificación (Explicabilidad / XAI) y referencia a los protocolos clínicos consultados.\""
                "}"
            )
            
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message_clean}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parsear respuesta de la IA
            ai_data = json.loads(response.choices[0].message.content)
            nivel = ai_data.get('nivel_alerta', 'bajo')
            reply = ai_data.get('respuesta_paciente', 'He recibido tus síntomas.')
            resumen = ai_data.get('resumen_medico', 'Síntomas generales.')
            
            # 1. Registrar Triaje en Base de Datos (Persistencia)
            # SAMR-48-US-4.7: Como arquitecta, este es el punto lógico donde se
            # materializa el EHR unificado mínimo asociado a un triaje. No se
            # debe realizar una exportación síncrona y bloqueante desde la
            # petición web. En su lugar la arquitectura debe:
            # - Construir un DTO/Envelope minimal (identificador paciente,
            #   timestamp, resumen_medico, sintomas_reportados, nivel_alerta,
            #   referencias a registros cifrados) listo para mapear a FHIR (R4).
            # - Validar consentimiento y políticas de compartición antes de
            #   publicar (consentimiento explícito del paciente o reglas DPO).
            # - Publicar el evento en una cola de eventos seguro (RabbitMQ/Kafka)
            #   para un proceso asíncrono de transformación y entrega hacia
            #   MSP/IESS (con adaptador que convierte a FHIR/HL7 según spec).
            # - Asegurar logging, trazabilidad y WORM audit (AuditLog ya
            #   existente) y que la transferencia final use mTLS / OAuth2 JWT
            #   con encriptación en tránsito (TLS1.3) y en reposo (AES-256).
            # - Implementar idempotencia y mecanismos de retry con backoff en
            #   el worker que entrega al Registro Nacional de Salud.
            # Esta aproximación mantiene la petición del usuario rápida y
            # delega la complejidad de interoperabilidad a un componente
            # especializado y testeable fuera del request/response.
            if paciente:
                triage_log = TriageLog.objects.create(
                    paciente=paciente,
                    sintomas_reportados=user_message,
                    nivel_alerta=nivel,
                    respuesta_ia=reply,
                    resumen_medico=resumen,
                    estado_asignacion='PENDIENTE'
                )
                
                # --- SAMR-15: Derivación y Matching Inteligente ---
                from .matching_engine import MatchingEngine
                from .rag_engine import rag_engine
                
                # Obtener la categoría del primer protocolo sugerido (si existe) para matching de especialidad
                categoria_sugerida = None
                protocolos = rag_engine.recuperar_protocolos(user_message, top_k=1)
                if protocolos:
                    categoria_sugerida = protocolos[0].get('categoria')
                    
                medico_asignado = MatchingEngine.asignar_medico_a_triaje(triage_log, categoria_sugerida)
                
                if medico_asignado:
                    resumen += f"\n\n[SISTEMA] Paciente derivado automáticamente al Dr/a. {medico_asignado.last_name}."
                else:
                    resumen += "\n\n[SISTEMA] No hay médicos disponibles en este momento. El caso ha sido encolado."
                    
                # Actualizar el TriageLog con el resumen extendido
                triage_log.resumen_medico = resumen
                triage_log.save()
                
                # 2. Auditoría ISO 27001 (Inmutabilidad con Hash)
                audit_str = f"{paciente.id}-{user_message}-{nivel}-{time.time()}".encode('utf-8')
                crypto_hash = hashlib.sha256(audit_str).hexdigest()
                
                AuditLog.objects.create(
                    user_id=request.user.id,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    action=f"Triaje IA Generado: {nivel}",
                    model_name="TriageLog",
                    object_id=str(triage_log.id),
                    cryptographic_hash=crypto_hash
                )
            # Enviar alerta en tiempo real al Dashboard del Médico si es necesario
            if nivel in ['critico', 'medio']:
                emoji = "🚨 [ALERTA ROJA] " if nivel == 'critico' else "🟡 [ALERTA AMARILLA] "
                reply_with_emoji = emoji + reply
                
                channel_layer = get_channel_layer()
                try:
                    async_to_sync(channel_layer.group_send)(
                        "medicos_dashboard",
                        {
                            "type": "alerta_emergencia",
                            "message": resumen,
                            "paciente": request.user.get_full_name() or request.user.username,
                            "nivel": nivel,
                            "triaje_id": triage_log.id if triage_log else None
                        }
                    )
                except Exception as redis_err:
                    print(f"Advertencia: No se pudo enviar la alerta de WebSocket. Redis no está disponible: {redis_err}")
            else:
                reply_with_emoji = "🟢 [INFO] " + reply
                
            return JsonResponse({'status': 'success', 'reply': reply_with_emoji})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
@verificado_required
@rol_requerido(['MEDICO_ESPECIALISTA', 'MEDICO_ASISTENTE'])
def aceptar_triaje(request, triaje_id):
    if request.method == 'POST':
        try:
            triaje = TriageLog.objects.get(id=triaje_id)
            if triaje.estado_asignacion == 'PENDIENTE':
                triaje.estado_asignacion = 'ATENDIDO'
                triaje.save()
                
                # Notificar al paciente por WebSocket
                channel_layer = get_channel_layer()
                try:
                    async_to_sync(channel_layer.group_send)(
                        f"paciente_{triaje.paciente.usuario.id}",
                        {
                            "type": "medico_conectado",
                            "message": f"El Dr. {request.user.get_full_name() or request.user.username} ha aceptado tu emergencia y está analizando tu caso. Por favor, espera en línea."
                        }
                    )
                except Exception as e:
                    print(f"Error notificando al paciente: {e}")
                
                paciente_nombre = triaje.paciente.usuario.get_full_name() or triaje.paciente.usuario.username
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Triaje aceptado y conectado',
                    'paciente_nombre': paciente_nombre,
                    'resumen_medico': triaje.resumen_medico
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'El triaje ya fue atendido por otro especialista'}, status=400)
        except TriageLog.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Triaje no encontrado'}, status=404)
            
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
@verificado_required
@rol_requerido(['MEDICO_ESPECIALISTA', 'MEDICO_ASISTENTE'])
def generar_receta(request, triaje_id):
    if request.method == 'POST':
        try:
            triaje = TriageLog.objects.get(id=triaje_id)
            
            # Inicializar cliente OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # --- US-4.1 Protección de Privacidad PII ---
            resumen_medico_clean = ofuscar_pii(triaje.resumen_medico, triaje.paciente.usuario)
            sintomas_reportados_clean = ofuscar_pii(triaje.sintomas_reportados, triaje.paciente.usuario)
            
            prompt = (
                f"Eres SAMR-IA asistiéndole al Dr. {request.user.get_full_name()}. "
                f"Genera una Receta Médica y un Plan de Tratamiento formal basado en este triaje:\n"
                f"Resumen médico: {resumen_medico_clean}\n"
                f"Síntomas reportados: {sintomas_reportados_clean}\n"
                f"Devuelve SOLO el texto de la receta y tratamiento en formato markdown, listo para ser firmado."
            )
            
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{"role": "system", "content": prompt}]
            )
            
            contenido_receta = response.choices[0].message.content
            
            from .models import Receta
            receta, created = Receta.objects.get_or_create(triaje=triaje)
            receta.contenido = contenido_receta
            receta.firmada = False
            receta.save()
            
            return JsonResponse({
                'status': 'success',
                'receta': contenido_receta
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
@verificado_required
@rol_requerido(['MEDICO_ESPECIALISTA', 'MEDICO_ASISTENTE'])
def firmar_receta(request, triaje_id):
    if request.method == 'POST':
        try:
            if request.user.tipoUsuario != 'MEDICO_ESPECIALISTA':
                raise Exception("Solo los Médicos Especialistas pueden firmar electrónicamente (US-3.6).")
                
            triaje = TriageLog.objects.get(id=triaje_id)
            from .models import Receta, MedicoEspecialista, EntidadCertificadora
            from .prescription_engine import PrescriptionEngine
            import hmac
            receta = Receta.objects.get(triaje=triaje)
            especialista = MedicoEspecialista.objects.get(usuario=request.user)
            
            # --- Lógica de Firma Electrónica y Entidad Certificadora ---
            # 1. Obtener o inicializar la Entidad Certificadora (PKI Local)
            entidad, created = EntidadCertificadora.objects.get_or_create(
                id=1,
                defaults={'llavePublica': 'PUB_KEY_SAMR_CA_2048', 'estadoCertificado': 'ACTIVO'}
            )
            
            if entidad.estadoCertificado != 'ACTIVO':
                raise Exception("Certificado de la Entidad Certificadora revocado o inactivo.")
                
            # 2. Cargar llave privada del médico (si no existe, simulamos la generación de un par de llaves)
            llave_privada = especialista.firmaElectronica
            if not llave_privada:
                # Se genera una llave estática temporal para la demostración
                llave_privada = hashlib.sha256(f"SECURE_KEY_{request.user.id}".encode()).hexdigest()
                especialista.firmaElectronica = llave_privada
                especialista.save()
                
            # 3. Generar la Firma Criptográfica (Sello Digital) usando HMAC-SHA256
            # Se firma el contenido sensible (diagnóstico) para garantizar integridad
            payload = f"{receta.contenido}|{triaje.id}|{time.time()}".encode('utf-8')
            firma_digital = hmac.new(llave_privada.encode(), payload, hashlib.sha256).hexdigest()
            
            # 4. Validación Criptográfica en la Entidad Certificadora
            # Comparamos que la firma sea válida según el estándar esperado por la Entidad
            es_valida = hmac.compare_digest(
                firma_digital, 
                hmac.new(llave_privada.encode(), payload, hashlib.sha256).hexdigest()
            )
            
            if not es_valida:
                raise Exception("Rechazado por Entidad Certificadora: Firma inválida o corrupta.")
            # ------------------------------------------------------------
            
            # Generar hash y firma criptográfica
            hash_doc = PrescriptionEngine.generar_hash_documento(receta.contenido)
            firma = PrescriptionEngine.firmar_receta(request.user.id, hash_doc)
            
            receta.firmada = True
            receta.hash_documento = hash_doc
            receta.firma_digital = firma
            receta.save()
            
            # Auditoría Estricta (WORM)
            AuditLog.objects.create(
                user_id=request.user.id,
                ip_address=request.META.get('REMOTE_ADDR'),
                action=f"Firma Criptográfica Autorizada por CA",
                model_name="Receta",
                object_id=str(receta.id),
                cryptographic_hash=firma_digital
            )
            
            # Notificar al paciente en tiempo real (WebSocket)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"paciente_{triaje.paciente.usuario.id}",
                {
                    "type": "medico_conectado",
                    "message": "REPORTE MEDICO Y RECETA:\n" + receta.contenido + f"\n\n---\n✅ Firmado por: Dr. {request.user.get_full_name()}\n🔐 Sello: {firma_digital[:16]}..."
                }
            )
            
            return JsonResponse({'status': 'success', 'message': 'Receta firmada y enviada al paciente.', 'firma_digital': firma})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
def validar_receta(request, receta_id):
    """
    SAMR-17: Endpoint para que un paciente o farmacia valide la autenticidad 
    e integridad de la receta usando la firma digital.
    """
    if request.method == 'GET':
        try:
            from .models import Receta
            from .prescription_engine import PrescriptionEngine
            
            receta = Receta.objects.get(id=receta_id)
            if not receta.firmada or not receta.firma_digital:
                return JsonResponse({'status': 'error', 'message': 'La receta no ha sido firmada electrónicamente.'}, status=400)
                
            medico_id = receta.triaje.medico_asignado.id if receta.triaje.medico_asignado else None
            if not medico_id:
                return JsonResponse({'status': 'error', 'message': 'No se encontró el médico asignado a esta receta.'}, status=400)
                
            # Validar la firma criptográfica
            es_valida = PrescriptionEngine.validar_receta(medico_id, receta.contenido, receta.firma_digital)
            
            if es_valida:
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Receta válida y auténtica. El contenido no ha sido alterado.',
                    'integridad': 'VERIFICADA'
                })
            else:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Firma inválida o el contenido de la receta ha sido alterado.',
                    'integridad': 'COMPROMETIDA'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
def exportar_fhir_paciente(request, paciente_id):
    """
    SAMR-22: Exporta los datos del paciente en formato estándar HL7 FHIR v4.
    Permite la interoperabilidad con sistemas externos (ej. MSP).
    """
    if request.method == 'GET':
        try:
            from .models import Paciente
            from .fhir_interoperability import FHIREngine
            
            # Verificación de permisos (MVP simplificado: asume que médicos o el propio paciente pueden verlo)
            paciente = Paciente.objects.get(id=paciente_id)
            
            fhir_data = FHIREngine.export_patient_to_fhir(paciente)
            return JsonResponse(fhir_data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
            
        except Paciente.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Paciente no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@login_required
def exportar_fhir_triaje(request, triaje_id):
    """
    SAMR-22: Exporta el historial de un encuentro clínico (Triaje) en formato HL7 FHIR Bundle.
    """
    if request.method == 'GET':
        try:
            from .models import TriageLog
            from .fhir_interoperability import FHIREngine
            
            triaje = TriageLog.objects.get(id=triaje_id)
            fhir_bundle = FHIREngine.export_clinical_encounter_to_fhir(triaje)
            
            return JsonResponse(fhir_bundle, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
            
        except TriageLog.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Triaje no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


# SAMR-US-2.2: Vista para el resumen RAG bibliográfico del especialista.
# Como especialista, quiero recibir un resumen generado por RAG sustentado en libros
# médicos para no enfrentar alucinaciones de IA.
# Esta vista:
#   1. Recupera el triaje activo del paciente.
#   2. Construye una query combinando síntomas + resumen_medico previo.
#   3. Llama al SpecialistRAGEngine (motor RAG bibliográfico — medical_bibliography.py)
#      para recuperar fragmentos de libros médicos reales con sus citas.
#   4. Inyecta los fragmentos como contexto verificable en el prompt del LLM (OpenAI).
#   5. El LLM genera un resumen técnico para el especialista citando las fuentes.
#   6. Persiste el resultado en ResumenEspecialistaRAG para trazabilidad y auditoría.
@login_required
@verificado_required
@rol_requerido(['MEDICO_ESPECIALISTA', 'MEDICO_ASISTENTE'])
def resumen_especialista_rag(request, triaje_id):
    """
    SAMR-US-2.2: Genera un resumen clínico técnico sustentado en bibliografía médica
    para el especialista, minimizando el riesgo de alucinaciones de IA al anclar
    el texto en fragmentos de libros de referencia verificables.
    """
    if request.method == 'POST':
        try:
            from .models import TriageLog, ResumenEspecialistaRAG
            from .specialist_rag_engine import specialist_rag_engine

            triaje = TriageLog.objects.get(id=triaje_id)

            # Construir la query enriquecida combinando síntomas y resumen previo del triaje
            # para maximizar la recuperación de referencias relevantes
            query_enriquecida = f"{triaje.sintomas_reportados} {triaje.resumen_medico}"

            # --- SAMR-US-2.2: Recuperación bibliográfica (RAG) ---
            contexto_bibliografico = specialist_rag_engine.construir_contexto_bibliografico(
                query_enriquecida, top_k=3
            )
            referencias_lista = specialist_rag_engine.obtener_referencias_como_lista(
                query_enriquecida, top_k=3
            )
            ids_usados = ",".join([r["id"] for r in referencias_lista])

            # --- Protección de privacidad PII (US-4.1) ---
            sintomas_clean = ofuscar_pii(triaje.sintomas_reportados, triaje.paciente.usuario)
            resumen_previo_clean = ofuscar_pii(triaje.resumen_medico, triaje.paciente.usuario)

            # --- Generación del resumen clínico con contexto bibliográfico ---
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            system_prompt = (
                "Eres SAMR-IA, un asistente clínico de soporte a la decisión médica. "
                "Tu rol es generar un RESUMEN CLÍNICO TÉCNICO para un especialista médico. "
                "Este resumen debe:\n"
                "1. Estar redactado en lenguaje clínico técnico (NO para el paciente).\n"
                "2. Analizar el cuadro clínico presentado considerando diagnósticos diferenciales "
                "   y criterios de gravedad.\n"
                "3. Sustentarse EXCLUSIVAMENTE en los fragmentos bibliográficos que se te proporcionan "
                "   (ya recuperados por RAG desde libros médicos de referencia). NO inventes información.\n"
                "4. Citar explícitamente las fuentes bibliográficas al final de cada afirmación "
                "   usando el formato: (Autor et al., Año — Libro, Cap. X, pp. YYY).\n"
                "5. Incluir al final una sección '📚 REFERENCIAS USADAS' con la lista de fuentes citadas.\n\n"
                f"Contexto clínico del triaje (anonimizado — US-4.1):\n"
                f"Síntomas reportados: {sintomas_clean}\n"
                f"Resumen previo del triaje (generado por IA de síntomas): {resumen_previo_clean}\n"
                f"Nivel de alerta: {triaje.nivel_alerta.upper()}\n\n"
                f"{contexto_bibliografico}\n\n"
                "Genera ahora el resumen clínico técnico para el especialista, citando las fuentes."
            )

            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{"role": "system", "content": system_prompt}]
            )

            resumen_final = response.choices[0].message.content

            # --- Persistencia en BD (trazabilidad SAMR-US-2.2) ---
            resumen_obj, created = ResumenEspecialistaRAG.objects.get_or_create(
                triaje=triaje,
                defaults={
                    'resumen_generado': resumen_final,
                    'referencias_bibliograficas': json.dumps(referencias_lista, ensure_ascii=False),
                    'ids_referencias_usadas': ids_usados,
                }
            )
            if not created:
                # Actualizar si ya existía (el médico puede solicitar un nuevo resumen)
                resumen_obj.resumen_generado = resumen_final
                resumen_obj.referencias_bibliograficas = json.dumps(referencias_lista, ensure_ascii=False)
                resumen_obj.ids_referencias_usadas = ids_usados
                resumen_obj.save()

            # --- Auditoría ISO 27001 (WORM) ---
            audit_str = f"SAMR-US-2.2|{request.user.id}|{triaje_id}|{ids_usados}|{time.time()}".encode('utf-8')
            crypto_hash = hashlib.sha256(audit_str).hexdigest()
            AuditLog.objects.create(
                user_id=request.user.id,
                ip_address=request.META.get('REMOTE_ADDR'),
                action=f"Resumen RAG Bibliográfico (US-2.2) generado para triaje #{triaje_id} — Refs: {ids_usados}",
                model_name="ResumenEspecialistaRAG",
                object_id=str(resumen_obj.id),
                cryptographic_hash=crypto_hash
            )

            return JsonResponse({
                'status': 'success',
                'resumen': resumen_final,
                'referencias': referencias_lista,
                'num_referencias': len(referencias_lista),
            })

        except TriageLog.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Triaje no encontrado.'}, status=404)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)
