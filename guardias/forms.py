from django import forms

from .models import (
    TipoActividad,
    RegistroActividad,
)


class TipoActividadForm(forms.ModelForm):

    class Meta:
        model = TipoActividad

        fields = [
            'nombre',
            'descripcion',
            'unidad',
            'valor',
            'activo',
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Guardia'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la actividad'
            }),

            'unidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. GUARDIA, HORA, DÍA'
            }),

            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),

            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class RegistroActividadForm(forms.ModelForm):

    class Meta:
        model = RegistroActividad

        fields = [
            'usuario',
            'tipo_actividad',
            'lugar',
            'fecha',
            'cantidad',
            'observacion',
        ]

        widgets = {
            'usuario': forms.Select(attrs={
                'class': 'form-select'
            }),

            'tipo_actividad': forms.Select(attrs={
                'class': 'form-select'
            }),

            'lugar': forms.Select(attrs={
                'class': 'form-select'
            }),

            'fecha': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),

            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),

            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observación'
            }),
        }