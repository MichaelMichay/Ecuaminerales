from django import forms
from .models import Insumo, CategoriaInsumo, LugarConsumo


class InsumoForm(forms.ModelForm):

    class Meta:

        model = Insumo

        fields = [
            'nombre_insumo',
            'tipo_insumo',
            'descripcion',
            'stock',
            'stock_minimo',
            'unidad_medida',
            'nivel_peligrosidad',
            'categoria',
            'estado'
        ]

        widgets = {

            'nombre_insumo': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'tipo_insumo': forms.Select(attrs={
                'class': 'form-select'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),

            'stock': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control'
            }),

            'unidad_medida': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'nivel_peligrosidad': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),

            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),

        }


class CategoriaInsumoForm(forms.ModelForm):

    class Meta:
        model = CategoriaInsumo

        fields = [
            'nombre_categoria',
            'descripcion'
        ]

        widgets = {

            'nombre_categoria': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),

        }


class LugarConsumoForm(forms.ModelForm):

    class Meta:
        model = LugarConsumo

        fields = [
            'nombre',
            'descripcion',
            'estado'
        ]

        widgets = {

            'nombre': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),

            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),

        }