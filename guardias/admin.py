from django.contrib import admin

from .models import (
    TipoActividad,
    RegistroActividad,
    LiquidacionMensual,
)


@admin.register(TipoActividad)
class TipoActividadAdmin(admin.ModelAdmin):

    list_display = (
        'nombre',
        'unidad',
        'valor',
        'activo',
        'fecha_creacion',
    )

    list_filter = (
        'activo',
    )

    search_fields = (
        'nombre',
        'descripcion',
    )

    list_editable = (
        'valor',
        'activo',
    )


@admin.register(RegistroActividad)
class RegistroActividadAdmin(admin.ModelAdmin):

    list_display = (
        'usuario',
        'tipo_actividad',
        'lugar',
        'fecha',
        'cantidad',
        'valor_unitario',
        'valor_total',
        'estado',
    )

    list_filter = (
        'estado',
        'tipo_actividad',
        'fecha',
    )

    search_fields = (
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'tipo_actividad__nombre',
    )

    date_hierarchy = 'fecha'


@admin.register(LiquidacionMensual)
class LiquidacionMensualAdmin(admin.ModelAdmin):

    list_display = (
        'usuario',
        'mes',
        'anio',
        'total_actividades',
        'total_generado',
        'estado',
        'fecha_generacion',
    )

    list_filter = (
        'estado',
        'mes',
        'anio',
    )

    search_fields = (
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
    )