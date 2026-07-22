from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Usuario
from datetime import date
import re

class RegistroForm(forms.ModelForm):
    tipo_usuario = forms.ChoiceField(choices=[('PACIENTE', 'Paciente'), ('FAMILIAR', 'Familiar'), ('MEDICO_ESPECIALISTA', 'Médico Especialista')], required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    password_confirm = forms.CharField(widget=forms.PasswordInput, required=True, label="Confirmar Contraseña")
    cedula_paciente_asociado = forms.CharField(required=False)
    
    # Campo Especialidad usando la BD
    from .models import Especialidad
    especialidad = forms.ModelChoiceField(
        queryset=Especialidad.objects.all(), 
        required=False, 
        empty_label="Seleccione Especialidad",
        widget=forms.Select(attrs={'class': 'form-control-custom w-100 bg-transparent text-light border-info', 'id': 'input_especialidad'})
    )
    
    registro_profesional = forms.CharField(required=False)

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
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Las contraseñas no coinciden.")
            
        tipo = cleaned_data.get('tipo_usuario')
        cedula_pac = cleaned_data.get('cedula_paciente_asociado')
        fecha_nacimiento = cleaned_data.get('fecha_nacimiento')
        
        # Si es familiar, debe proporcionar cédula
        if tipo == 'FAMILIAR' and not cedula_pac:
            self.add_error('cedula_paciente_asociado', "Debes proporcionar la cédula del paciente.")

        # Si es médico, debe proporcionar especialidad y registro profesional
        if tipo == 'MEDICO_ESPECIALISTA':
            especialidad = cleaned_data.get('especialidad')
            registro_profesional = cleaned_data.get('registro_profesional')
            if not especialidad or especialidad.strip() == '':
                self.add_error('especialidad', "Debes proporcionar tu especialidad.")
            if not registro_profesional or registro_profesional.strip() == '':
                self.add_error('registro_profesional', "Debes proporcionar tu registro profesional.")

        # Si es paciente, validamos edad y alergias
        if tipo == 'PACIENTE':
            alergias = cleaned_data.get('alergias')
            if not alergias or alergias.strip() == '':
                cleaned_data['alergias'] = 'Ninguna'
                
            if fecha_nacimiento:
                today = date.today()
                age = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
                if age < 18:
                    self.add_error('fecha_nacimiento', "Los menores de edad deben ser registrados por un Familiar.")

        return cleaned_data
