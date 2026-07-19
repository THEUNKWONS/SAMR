from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Usuario
from datetime import date
import re

class RegistroForm(forms.ModelForm):
    tipo_usuario = forms.ChoiceField(choices=[('PACIENTE', 'Paciente'), ('FAMILIAR', 'Familiar')], required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    cedula_paciente_asociado = forms.CharField(required=False)

    class Meta:
        model = Usuario
        fields = ['nombres', 'apellidos', 'dni', 'telefono_principal', 'email', 'fecha_nacimiento']

    # Renombrando campos que no coinciden directamente con el modelo de manera mágica
    nombres = forms.CharField(max_length=150, required=True)
    apellidos = forms.CharField(max_length=150, required=True)
    alergias = forms.CharField(widget=forms.Textarea, required=False)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        try:
            validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(list(e.messages))
        
        # Validación extra de fortaleza
        if not re.search(r'\d', password) or not re.search(r'[A-Za-z]', password):
            raise forms.ValidationError("La contraseña debe contener al menos letras y números.")
            
        return password

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if not dni.isdigit() or len(dni) < 10:
            raise forms.ValidationError("La cédula debe contener al menos 10 dígitos numéricos.")
        if Usuario.objects.filter(dni=dni).exists():
            raise forms.ValidationError("Esta cédula ya está registrada.")
        return dni

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(username=email).exists() or Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya se encuentra en uso.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_usuario')
        cedula_pac = cleaned_data.get('cedula_paciente_asociado')
        fecha_nacimiento = cleaned_data.get('fecha_nacimiento')
        
        # Si es familiar, debe proporcionar cédula
        if tipo == 'FAMILIAR' and not cedula_pac:
            self.add_error('cedula_paciente_asociado', "Debes proporcionar la cédula del paciente.")

        # Si es paciente, validamos edad y alergias
        if tipo == 'PACIENTE':
            alergias = cleaned_data.get('alergias')
            if not alergias or alergias.strip() == '':
                self.add_error('alergias', "El campo de alergias es obligatorio (Escribe 'Ninguna' si no tienes).")
                
            if fecha_nacimiento:
                today = date.today()
                age = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
                if age < 18:
                    self.add_error('fecha_nacimiento', "Los menores de edad deben ser registrados por un Familiar.")

        return cleaned_data
