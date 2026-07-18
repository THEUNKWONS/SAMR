from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Usuario

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            # Simulador de OTP: enviamos un código al terminal
            request.session['pre_otp_user'] = user.id
            print(f"\n[SISTEMA 2FA] Código OTP para el usuario {user.username}: 123456\n")
            return redirect('otp_verify')
        else:
            messages.error(request, 'Credenciales inválidas.')
    return render(request, 'auth/login.html')

def otp_verify_view(request):
    if 'pre_otp_user' not in request.session:
        return redirect('login')
        
    if request.method == 'POST':
        codigo = request.POST.get('otp_code')
        if codigo == '123456': # Código mock para prototipo local
            user_id = request.session['pre_otp_user']
            user = Usuario.objects.get(id=user_id)
            login(request, user)
            del request.session['pre_otp_user']
            
            # Verificar LOPDP
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
        nombres = request.POST.get('nombres')
        apellidos = request.POST.get('apellidos')
        dni = request.POST.get('dni')
        telefono = request.POST.get('telefono')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Validar si el usuario ya existe
        if Usuario.objects.filter(username=email).exists():
            messages.error(request, 'El correo ya está registrado.')
        else:
            # Crear el usuario
            nuevo_usuario = Usuario.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=nombres,
                last_name=apellidos,
                dni=dni,
                telefono_principal=telefono,
                tipoUsuario='PACIENTE'
            )
            messages.success(request, '¡Registro exitoso! Por favor, inicia sesión.')
            return redirect('login')
            
    return render(request, 'auth/registro.html')

# --- Vistas Protegidas Internas ---

@login_required
def inicio(request):
    if not request.user.acepto_terminos_lopdp:
        return redirect('terminos_lopdp')
    return render(request, 'inicio.html')

@login_required
def triaje_inteligente(request):
    return render(request, 'triaje.html')

@login_required
def registro_multimodal(request):
    return render(request, 'registro.html')

@login_required
def panel_especialista(request):
    return render(request, 'panel_medico.html')

@login_required
def historial_clinico(request):
    return render(request, 'historial.html')
