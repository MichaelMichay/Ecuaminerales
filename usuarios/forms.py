from django import forms
from .models import Usuario, Rol
from django.core.exceptions import ValidationError
import re


def validar_cedula_ecuador(cedula):

    if not cedula.isdigit():
        return False

    if len(cedula) != 10:
        return False

    provincia = int(cedula[:2])

    if provincia < 1 or provincia > 24:
        return False

    tercer_digito = int(cedula[2])

    if tercer_digito >= 6:
        return False

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]

    suma = 0

    for i in range(9):

        valor = int(cedula[i]) * coeficientes[i]

        if valor >= 10:
            valor -= 9

        suma += valor

    verificador = (10 - (suma % 10)) % 10

    return verificador == int(cedula[9])


class UsuarioForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Contraseña'
    )

    class Meta:

        model = Usuario

        fields = [
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'cedula',
            'telefono',
            'rol',
            'estado',
        ]

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_telefono(self):

        telefono = self.cleaned_data['telefono']

        if not re.match(r'^09\d{8}$', telefono):

            raise ValidationError(
                'El número debe iniciar con 09 y tener 10 dígitos.'
            )

        return telefono

    def clean_first_name(self):

        nombres = self.cleaned_data['first_name']

        if len(nombres) < 2:
            raise ValidationError(
                'Debe ingresar al menos 2 caracteres.'
            )

        if not nombres.replace(' ', '').isalpha():
            raise ValidationError(
                'Los nombres solo pueden contener letras.'
            )

        return nombres

    def clean_last_name(self):

        apellidos = self.cleaned_data['last_name']

        if len(apellidos) < 2:
            raise ValidationError(
                'Debe ingresar al menos 2 caracteres.'
            )

        if not apellidos.replace(' ', '').isalpha():
            raise ValidationError(
                'Los apellidos solo pueden contener letras.'
            )

        return apellidos

    def clean_cedula(self):

        cedula = self.cleaned_data['cedula']

        if not validar_cedula_ecuador(cedula):
            raise ValidationError(
                'La cédula ecuatoriana no es válida.'
            )

        return cedula

    def clean_password(self):

        password = self.cleaned_data['password']

        if len(password) < 8:
            raise ValidationError(
                'La contraseña debe tener mínimo 8 caracteres.'
            )

        return password


class UsuarioEditarForm(forms.ModelForm):

    class Meta:
        model = Usuario

        fields = [
            'username',
            'email',
            'telefono',
            'rol',
            'estado',
        ]

        widgets = {
            'username':forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_telefono(self):

        telefono = self.cleaned_data['telefono']

        if not re.match(r'^09\d{8}$', telefono):
            raise ValidationError(
                'El número debe iniciar con 09 y tener 10 dígitos.'
            )

        return telefono
class PerfilUsuarioForm(forms.ModelForm):

    nueva_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Opcional',
            'id': 'id_nueva_password'
        }),
        label='Nueva contraseña'
    )

    class Meta:
        model = Usuario

        fields = [
            'username',
            'email',
            'telefono',
        ]

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):

        username = self.cleaned_data['username']

        existe = Usuario.objects.filter(
            username=username
        ).exclude(
            pk=self.instance.pk
        ).exists()

        if existe:
            raise ValidationError(
                'Este nombre de usuario ya existe.'
            )

        return username

    def clean_telefono(self):

        telefono = self.cleaned_data['telefono']

        if not re.match(r'^09\d{8}$', telefono):
            raise ValidationError(
                'El número debe iniciar con 09 y tener 10 dígitos.'
            )

        return telefono

    def clean_nueva_password(self):

        password = self.cleaned_data.get('nueva_password')

        if password and len(password) < 8:
            raise ValidationError(
                'La contraseña debe tener mínimo 8 caracteres.'
            )

        return password
class CambiarPasswordForm(forms.Form):

    password = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_password'
        })
    )

    confirmar_password = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'id_confirmar_password'
        })
    )

    def clean_password(self):
        password = self.cleaned_data['password']

        if len(password) < 8:
            raise ValidationError(
                'La contraseña debe tener mínimo 8 caracteres.'
            )

        return password

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirmar_password = cleaned_data.get('confirmar_password')

        if password and confirmar_password and password != confirmar_password:
            raise ValidationError(
                'Las contraseñas no coinciden.'
            )

        return cleaned_data
class RolForm(forms.ModelForm):

    class Meta:
        model = Rol
        fields = ['nombre_rol']

        widgets = {
            'nombre_rol': forms.TextInput(attrs={'class': 'form-control'}),
        }