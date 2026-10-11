from django import forms
from django.contrib import admin

from .models import AjusteCategoria, Comunicado, Producto


@admin.register(Comunicado)
class ComunicadoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha_publicacion', 'publicado')
    list_filter = ('publicado',)
    list_editable = ('publicado',)
    search_fields = ('titulo', 'resumen')
    date_hierarchy = 'fecha_publicacion'


class AjusteCategoriaForm(forms.ModelForm):
    class Meta:
        model = AjusteCategoria
        fields = '__all__'
        widgets = {'color': forms.TextInput(attrs={'type': 'color'})}


@admin.register(AjusteCategoria)
class AjusteCategoriaAdmin(admin.ModelAdmin):
    """Solo hace falta crear un ajuste para ocultar, ordenar o dar color a una categoría."""
    form = AjusteCategoriaForm
    list_display = ('categoria', 'visible', 'mostrar_insumos', 'detalle_stock', 'orden')
    list_editable = ('visible', 'mostrar_insumos', 'detalle_stock', 'orden')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'orden', 'activo')
    list_filter = ('categoria', 'activo')
    list_editable = ('orden', 'activo')
    search_fields = ('nombre', 'descripcion')