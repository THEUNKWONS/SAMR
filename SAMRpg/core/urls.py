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
    path('registro-multimodal/', views.registro_multimodal, name='registro_multimodal'),
    path('triaje/', views.triaje_inteligente, name='triaje_inteligente'),
    path('panel-medico/', views.panel_especialista, name='panel_especialista'),
    path('historial/', views.historial_clinico, name='historial_clinico'),
]
