from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_paciente_view, name='registro_paciente'),
    path('otp-verify/', views.otp_verify_view, name='otp_verify'),
    path('terminos-lopdp/', views.terminos_lopdp_view, name='terminos_lopdp'),
    path('logout/', views.logout_view, name='logout'),

    # Internas
    path('', views.inicio, name='inicio'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('gestionar-familiar/<int:familiar_id>/', views.gestionar_solicitud_familiar, name='gestionar_solicitud_familiar'),
    path('triaje/', views.triaje_inteligente, name='triaje_inteligente'),
    path('panel-medico/', views.panel_especialista, name='panel_especialista'),
    path('historial/', views.historial_clinico, name='historial_clinico'),
    
    # API endpoints
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),
    path('api/triaje/<int:triaje_id>/aceptar/', views.aceptar_triaje, name='aceptar_triaje'),
    path('api/triaje/<int:triaje_id>/generar_receta/', views.generar_receta, name='generar_receta'),
    path('api/triaje/<int:triaje_id>/firmar_receta/', views.firmar_receta, name='firmar_receta'),
    path('api/triaje/<int:triaje_id>/chat/', views.medico_chat_api, name='medico_chat_api'),
    path('api/triaje/<int:triaje_id>/ambulancia/', views.solicitar_ambulancia, name='solicitar_ambulancia'),
]
