from django.urls import path

from . import views


urlpatterns = [

    # =====================================================
    # ACTIVIDADES Y TARIFAS
    # =====================================================

    path(
        'actividades/',
        views.lista_actividades,
        name='guardias_actividades'
    ),

    path(
        'actividades/nueva/',
        views.crear_actividad,
        name='crear_actividad'
    ),

    path(
        'actividades/editar/<int:id>/',
        views.editar_actividad,
        name='editar_actividad'
    ),

    # =====================================================
    # REGISTRO DE ACTIVIDADES
    # =====================================================

    path(
        'registros/',
        views.lista_registros,
        name='guardias_registros'
    ),

    path(
        'registros/nuevo/',
        views.registrar_actividad,
        name='registrar_actividad'
    ),
    path(
    'mis-ingresos/',
    views.mis_ingresos,
    name='mis_ingresos'
    ),
    path(
    'liquidaciones/aceptar/<int:liquidacion_id>/',
    views.aceptar_liquidacion,
    name='aceptar_liquidacion'
    ),
    path(
    'liquidaciones/impugnar/<int:liquidacion_id>/',
    views.impugnar_liquidacion,
    name='impugnar_liquidacion'
    ),

]