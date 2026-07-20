from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import time
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
import time
from datetime import date
import hashlib

def rol_requerido(roles_permitidos):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.tipoUsuario not in roles_permitidos:
                messages.error(request, "Acceso denegado: No tienes permisos para ver esta página.")
                return redirect('inicio')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def verificado_required(view_func):
    """Decorador para bloquear acceso a Familiares con estado PENDIENTE."""
    def wrapper(request, *args, **kwargs):
        if request.user.tipoUsuario == 'FAMILIAR':
            try:
                familiar = request.user.perfil_familiar
                if familiar.estado_solicitud == 'PENDIENTE':
                    messages.error(request, "Tu cuenta debe ser verificada por el paciente antes de acceder a esta sección.")
                    return redirect('inicio')
            except:
                pass
        return view_func(request, *args, **kwargs)
    return wrapper

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            # Generar OTP de 6 dígitos
            otp = str(random.randint(100000, 999999))
            request.session['pre_otp_user'] = user.id
            request.session['otp_code'] = otp
            request.session['otp_timestamp'] = time.time()
            
            # Enviar correo (En desarrollo se imprime en consola)
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
                
            messages.success(request, 'Código OTP enviado a tu correo.')
            return redirect('otp_verify')
        else:
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
            
            # Limpiar sesión
            del request.session['pre_otp_user']
            del request.session['otp_code']
            del request.session['otp_timestamp']
            
            messages.success(request, f'¡Bienvenido de nuevo, {user.first_name}!')
            
            if not user.acepto_terminos_lopdp:
                return redirect('terminos_lopdp')
            return redirect('inicio')
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
    triajes_pendientes = TriageLog.objects.filter(estado_asignacion='PENDIENTE').order_by('-timestamp')
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

            # Inicializar cliente OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Prompts y configuración
            system_instruction = (
                f"Eres SAMR-IA, un asistente de triaje médico avanzado. "
                f"Estás evaluando a un paciente con el siguiente contexto clínico anonimizado:\n"
                f"{contexto_clinico}\n\n"
                "Analiza los síntomas del paciente basándote estrictamente en este contexto y devuelve SIEMPRE un JSON válido con la siguiente estructura exacta: "
                "{"
                "  \"nivel_alerta\": \"critico\" (para emergencias vitales inminentes como dolor de pecho, riesgo de desmayo, pérdida de consciencia, sangrado severo, dificultad para respirar o alergias graves), \"medio\" (infecciones, dolor agudo sin riesgo de vida inmediato) o \"bajo\" (consultas generales, síntomas leves); "
                "  \"respuesta_paciente\": \"Mensaje empático, claro y directo. Si es crítico o medio, debes informarle al paciente que has emitido una ALERTA INMEDIATA al panel de los médicos y que un especialista se conectará con él en breve a través de la plataforma para una teleconsulta. No lo mandes a llamar al 911, asume que nuestra plataforma gestionará la emergencia.\"; "
                "  \"resumen_medico\": \"Resumen técnico para el especialista con posible pre-diagnóstico y justificación (Explicabilidad / XAI)\""
                "}"
            )
            
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parsear respuesta de la IA
            ai_data = json.loads(response.choices[0].message.content)
            nivel = ai_data.get('nivel_alerta', 'bajo')
            reply = ai_data.get('respuesta_paciente', 'He recibido tus síntomas.')
            resumen = ai_data.get('resumen_medico', 'Síntomas generales.')
            
            # 1. Registrar Triaje en Base de Datos (Persistencia)
            if paciente:
                triage_log = TriageLog.objects.create(
                    paciente=paciente,
                    sintomas_reportados=user_message,
                    nivel_alerta=nivel,
                    respuesta_ia=reply,
                    resumen_medico=resumen,
                    estado_asignacion='PENDIENTE'
                )
                
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
            
            prompt = (
                f"Eres SAMR-IA asistiéndole al Dr. {request.user.get_full_name()}. "
                f"Genera una Receta Médica y un Plan de Tratamiento formal basado en este triaje:\n"
                f"Resumen médico: {triaje.resumen_medico}\n"
                f"Síntomas reportados: {triaje.sintomas_reportados}\n"
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
            triaje = TriageLog.objects.get(id=triaje_id)
            from .models import Receta
            receta = Receta.objects.get(triaje=triaje)
            
            receta.firmada = True
            receta.save()
            
            # Auditoría
            audit_str = f"{receta.id}-FIRMADA-{request.user.id}-{time.time()}".encode('utf-8')
            crypto_hash = hashlib.sha256(audit_str).hexdigest()
            
            AuditLog.objects.create(
                user_id=request.user.id,
                ip_address=request.META.get('REMOTE_ADDR'),
                action=f"Receta Firmada Electrónicamente",
                model_name="Receta",
                object_id=str(receta.id),
                cryptographic_hash=crypto_hash
            )
            
            # Notificar al paciente
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"paciente_{triaje.paciente.usuario.id}",
                {
                    "type": "medico_conectado",
                    "message": "REPORTE MEDICO Y RECETA:\n" + receta.contenido + f"\n\n---\n✅ Firmado electrónicamente por: Dr. {request.user.get_full_name()}"
                }
            )
            
            return JsonResponse({'status': 'success', 'message': 'Receta firmada y enviada al paciente.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
