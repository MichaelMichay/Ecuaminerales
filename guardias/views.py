from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from datetime import date
from django.urls import reverse
from itertools import groupby
from .forms import TipoActividadForm, RegistroActividadForm
from .models import TipoActividad, RegistroActividad, LiquidacionMensual
from decimal import Decimal
from django.utils import timezone



# =========================================================
# ACTIVIDADES Y TARIFAS
# =========================================================

@login_required
def lista_actividades(request):

    actividades = TipoActividad.objects.all().order_by('nombre')

    return render(
        request,
        'guardias/actividades.html',
        {
            'actividades': actividades
        }
    )


@login_required
def crear_actividad(request):

    if request.method == 'POST':

        form = TipoActividadForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Actividad creada correctamente.'
            )

            return redirect('guardias_actividades')

    else:

        form = TipoActividadForm()

    return render(
        request,
        'guardias/crear_actividad.html',
        {
            'form': form
        }
    )


@login_required
def editar_actividad(request, id):

    actividad = get_object_or_404(
        TipoActividad,
        id=id
    )

    if request.method == 'POST':

        form = TipoActividadForm(
            request.POST,
            instance=actividad
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                'Actividad actualizada correctamente.'
            )

            return redirect('guardias_actividades')

    else:

        form = TipoActividadForm(
            instance=actividad
        )

    return render(
        request,
        'guardias/editar_actividad.html',
        {
            'form': form,
            'actividad': actividad
        }
    )


# =========================================================
# REGISTRO DE ACTIVIDADES
# =========================================================

@login_required
def lista_registros(request):

    fecha_str = request.GET.get('fecha')

    if fecha_str:
        try:
            fecha_seleccionada = date.fromisoformat(fecha_str)
        except ValueError:
            fecha_seleccionada = date.today()
    else:
        fecha_seleccionada = date.today()

    registros = (
        RegistroActividad.objects
        .select_related('usuario', 'tipo_actividad', 'lugar')
        .filter(fecha=fecha_seleccionada)
        .order_by('usuario__first_name', 'usuario__last_name', '-id')
    )

    total_generado = (
        registros.aggregate(total=Sum('valor_total'))['total'] or 0
    )

    total_registros = registros.count()

    total_trabajadores = (
        registros.values('usuario').distinct().count()
    )

    grupos = []
    for usuario, items in groupby(registros, key=lambda r: r.usuario):
        items = list(items)
        subtotal = sum(r.valor_total for r in items)
        grupos.append({
            'usuario': usuario,
            'registros': items,
            'subtotal': subtotal,
        })

    return render(
        request,
        'guardias/registros.html',
        {
            'grupos': grupos,
            'total_generado': total_generado,
            'total_registros': total_registros,
            'total_trabajadores': total_trabajadores,
            'fecha_seleccionada': fecha_seleccionada,
            'hoy': date.today(),
        }
    )
@login_required
def registrar_actividad(request):

    usuario_id = request.GET.get('usuario_id') or request.POST.get('usuario')
    fecha_param = request.GET.get('fecha')

    if request.method == 'POST':

        form = RegistroActividadForm(request.POST)

        if form.is_valid():

            registro = form.save(commit=False)

            actividad = registro.tipo_actividad
            registro.valor_unitario = actividad.valor
            registro.valor_total = registro.cantidad * registro.valor_unitario
            registro.estado = 'PENDIENTE'

            registro.save()

            messages.success(request, 'Actividad registrada correctamente.')

            # Vuelve al día donde se estaba trabajando
            return redirect(f"{reverse('guardias_registros')}?fecha={registro.fecha}")

    else:

        initial = {}

        if usuario_id:
            initial['usuario'] = usuario_id

        if fecha_param:
            initial['fecha'] = fecha_param
        else:
            initial['fecha'] = date.today()

        form = RegistroActividadForm(initial=initial)

    return render(
        request,
        'guardias/registrar_actividad.html',
        {'form': form}
    )
@login_required
def mis_ingresos(request):

    hoy = date.today()

    try:
        mes = int(request.GET.get('mes', hoy.month))
    except (TypeError, ValueError):
        mes = hoy.month

    try:
        anio = int(request.GET.get('anio', hoy.year))
    except (TypeError, ValueError):
        anio = hoy.year

    # Solo registros del usuario que inició sesión
    registros = RegistroActividad.objects.filter(
        usuario=request.user,
        fecha__year=anio,
        fecha__month=mes
    ).select_related(
        'tipo_actividad',
        'lugar'
    ).order_by('fecha')

    total_generado = registros.aggregate(
        total=Sum('valor_total')
    )['total'] or Decimal('0.00')

    total_actividades = registros.count()

    dias_trabajados = registros.values(
        'fecha'
    ).distinct().count()

    liquidacion = LiquidacionMensual.objects.filter(
        usuario=request.user,
        mes=mes,
        anio=anio
    ).first()

    context = {
        'registros': registros,
        'liquidacion': liquidacion,
        'mes': mes,
        'anio': anio,
        'total_generado': total_generado,
        'total_actividades': total_actividades,
        'dias_trabajados': dias_trabajados,
    }

    return render(
        request,
        'guardias/mis_ingresos.html',
        context
    )
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone


@login_required
def aceptar_liquidacion(request, liquidacion_id):

    liquidacion = get_object_or_404(
        LiquidacionMensual,
        id=liquidacion_id,
        usuario=request.user
    )

    # Solo se puede aceptar una liquidación abierta
    if liquidacion.estado != 'ABIERTA':
        messages.warning(
            request,
            'Esta liquidación ya fue procesada y no puede ser aceptada nuevamente.'
        )
        return redirect('mis_ingresos')

    if request.method == 'POST':

        liquidacion.estado = 'ACEPTADA'
        liquidacion.fecha_aceptacion = timezone.now()
        liquidacion.save(
            update_fields=[
                'estado',
                'fecha_aceptacion'
            ]
        )

        messages.success(
            request,
            'La liquidación mensual fue aceptada correctamente.'
        )

    return redirect(
        f"{reverse('mis_ingresos')}?mes={liquidacion.mes}&anio={liquidacion.anio}"
    )


@login_required
def impugnar_liquidacion(request, liquidacion_id):

    liquidacion = get_object_or_404(
        LiquidacionMensual,
        id=liquidacion_id,
        usuario=request.user
    )

    # Solo se puede impugnar una liquidación abierta
    if liquidacion.estado != 'ABIERTA':
        messages.warning(
            request,
            'Esta liquidación ya fue procesada y no puede ser impugnada nuevamente.'
        )
        return redirect('mis_ingresos')

    if request.method == 'POST':

        observacion = request.POST.get(
            'observacion_impugnacion',
            ''
        ).strip()

        if not observacion:

            messages.error(
                request,
                'Debe indicar el motivo de la impugnación.'
            )

            return redirect(
                f"{reverse('mis_ingresos')}?mes={liquidacion.mes}&anio={liquidacion.anio}"
            )

        liquidacion.estado = 'IMPUGNADA'
        liquidacion.observacion_impugnacion = observacion
        liquidacion.fecha_impugnacion = timezone.now()

        liquidacion.save(
            update_fields=[
                'estado',
                'observacion_impugnacion',
                'fecha_impugnacion'
            ]
        )

        messages.success(
            request,
            'La liquidación fue impugnada y enviada para revisión.'
        )

    return redirect(
        f"{reverse('mis_ingresos')}?mes={liquidacion.mes}&anio={liquidacion.anio}"
    )