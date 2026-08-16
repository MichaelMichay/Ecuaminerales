from django import forms

from .models import (
    OrdenTiro,
    DetalleOrdenTiro,
    MaterialOrden
)
from usuarios.models import Usuario


class OrdenTiroForm(forms.ModelForm):

    class Meta:
        model = OrdenTiro

        fields = [
            'cantidad_tiros',
            'metros_mecha',
            'perforista',
            'bodeguero',
            'lugar',
            'observacion',
        ]

        widgets = {

            'cantidad_tiros': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),

            'metros_mecha': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.1'
            }),

            'perforista': forms.Select(attrs={
                'class': 'form-select'
            }),

            'bodeguero': forms.Select(attrs={
                'class': 'form-select'
            }),

            'lugar': forms.Select(attrs={
                'class': 'form-select'
            }),

            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),

        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # SOLO PERFORISTAS
        self.fields['perforista'].queryset = Usuario.objects.filter(
            rol__nombre_rol='Perforista'
        ).order_by('first_name', 'last_name')

        # SOLO BODEGUEROS
        self.fields['bodeguero'].queryset = Usuario.objects.filter(
            rol__nombre_rol='Bodeguero'
        ).order_by('first_name', 'last_name')

        self.fields['perforista'].empty_label = "Seleccione perforista"
        self.fields['bodeguero'].empty_label = "Seleccione bodeguero"


class DetalleOrdenTiroForm(forms.ModelForm):

    class Meta:

        model = DetalleOrdenTiro

        fields = [
            'insumo',
            'cantidad',
        ]

        widgets = {

            'insumo': forms.Select(attrs={
                'class': 'form-select'
            }),

            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

        }

class MaterialOrdenForm(forms.ModelForm):

    class Meta:
        model = MaterialOrden

        fields = [
            'insumo',
            'cantidad',
            'observacion'
        ]

        widgets = {

            'insumo': forms.Select(attrs={
                'class': 'form-select'
            }),

            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'observacion': forms.TextInput(attrs={
                'class': 'form-control'
            })

        }