import os
import json
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse
from decimal import Decimal
from io import BytesIO
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image as RLImage,
)

from .models import (
    OrdenTiro,
    DetalleOrdenTiro,
    Despacho,
    DetalleDespacho,
    MaterialOrden,
)
from .forms import OrdenTiroForm, DetalleOrdenTiroForm, MaterialOrdenForm

from inventario.models import Insumo, MovimientoInventario
from reportes.models import Notificacion, Auditoria
from usuarios.models import Usuario
from usuarios.decorators import rol_requerido

@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def panel_bodeguero(request):

    ordenes = OrdenTiro.objects.filter(
        estado='PENDIENTE'
    ).order_by('-fecha_orden')

    ordenes_materiales = []

    for orden in ordenes:

        materiales = MaterialOrden.objects.filter(
            orden_tiro=orden
        ).select_related('insumo')

        ordenes_materiales.append({
            'orden': orden,
            'materiales': materiales
        })

    return render(
        request,
        'despachos/panel_bodeguero.html',
        {
            'ordenes_materiales': ordenes_materiales
        }
    )

@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def aprobar_orden_bodeguero(request, id):

    orden = OrdenTiro.objects.get(id=id)

    materiales = MaterialOrden.objects.filter(
        orden_tiro=orden
    )

    if not materiales.exists():

        messages.error(
            request,
            'La orden no tiene materiales configurados.'
        )

        return redirect('panel_bodeguero')
    
   
    # VALIDAR STOCK

    for material in materiales:

        if material.insumo.stock < material.cantidad:

            messages.error(
                request,
                f'Stock insuficiente de {material.insumo.nombre_insumo}. '
                f'Stock actual: {material.insumo.stock}'
            )

            return redirect('panel_bodeguero')

    # CREAR DESPACHO (mover esto ANTES del bucle de movimientos)
    despacho = Despacho.objects.create(
        orden_tiro=orden,
        bodeguero=request.user,
        estado='ENTREGADO',
        observacion='Despacho generado automáticamente.'
    )
    # DESCONTAR INVENTARIO Y REGISTRAR KARDEX

    for material in materiales:

        insumo = material.insumo

        stock_anterior = insumo.stock

        insumo.stock -= material.cantidad
        insumo.save()

        MovimientoInventario.objects.create(
            tipo_movimiento='SALIDA',
            cantidad=material.cantidad,
            stock_anterior=stock_anterior,
            stock_actual=insumo.stock,
            observacion=(
                f'Salida por orden {orden.codigo_orden}'
            ),
            insumo=insumo,
            usuario=request.user,
            despacho=despacho,
        )

    # NOTIFICAR STOCK BAJO

    usuarios_notificar = Usuario.objects.filter(
        rol__nombre_rol__in=[
            'Administrador',
            'Bodeguero'
        ]
    )

    for material in materiales:

        insumo = material.insumo

        if insumo.stock <= insumo.stock_minimo:

            for usuario in usuarios_notificar:

                Notificacion.objects.create(
                    usuario=usuario,
                    mensaje=(
                        f'El insumo '
                        f'{insumo.nombre_insumo} '
                        f'está en stock bajo.'
                    )
                )

    

    # DETALLE DEL DESPACHO

    for material in materiales:

        DetalleDespacho.objects.create(
            despacho=despacho,
            insumo=material.insumo,
            cantidad=material.cantidad
        )

    # ACTUALIZAR ESTADO DE LA ORDEN

    orden.estado = 'DESPACHADA'
    orden.save()

    # AUDITORÍA

    Auditoria.objects.create(
        usuario=request.user,
        accion='APROBACIÓN DE ORDEN',
        descripcion=(
            f'Se aprobó la orden '
            f'{orden.codigo_orden}. '
            f'Perforista: '
            f'{orden.perforista.username}. '
            f'Se generó despacho y '
            f'se descontó inventario.'
        )
    )

    messages.success(
        request,
        'Orden aprobada correctamente. '
        'Se generó el despacho y se actualizó el inventario.'
    )

    return redirect('panel_bodeguero')

@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def rechazar_orden_bodeguero(request, id):

    orden = OrdenTiro.objects.get(id=id)

    orden.estado = 'RECHAZADA'

    orden.save()

    Auditoria.objects.create(
        usuario=request.user,
        accion='RECHAZO DE ORDEN',
        descripcion=f'Se rechazó la orden {orden.codigo_orden}.'
    )

    messages.warning(
        request,
        'Orden rechazada correctamente.'
    )

    return redirect('panel_bodeguero')

@login_required
@rol_requerido(['Administrador', 'Bodeguero', 'Perforista'])
def lista_ordenes(request):
    buscar = request.GET.get('buscar')
    estado = request.GET.get('estado')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    ordenes = OrdenTiro.objects.all().order_by('-fecha_orden')

    if buscar:
        ordenes = ordenes.filter(codigo_orden__icontains=buscar)

    if estado:
        ordenes = ordenes.filter(estado=estado)

    if fecha_inicio:
        ordenes = ordenes.filter(fecha_orden__date__gte=fecha_inicio)

    if fecha_fin:
        ordenes = ordenes.filter(fecha_orden__date__lte=fecha_fin)

    paginator = Paginator(ordenes, 10)
    page_number = request.GET.get('page')
    ordenes = paginator.get_page(page_number)

    return render(request, 'despachos/lista_ordenes.html', {
        'ordenes': ordenes,
        'buscar': buscar,
        'estado': estado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'page_obj': ordenes
    })
def calcular_materiales(cantidad_tiros, metros_mecha=1.8):

    dinamita = cantidad_tiros * 1

    fulminantes = cantidad_tiros * 1

    mecha = (cantidad_tiros * float(metros_mecha)) + 2

    nitrato = cantidad_tiros * 5

    return {
        'dinamita': dinamita,
        'fulminantes': fulminantes,
        'mecha': mecha,
        'nitrato': nitrato
    }


@login_required
@rol_requerido(['Administrador', 'Bodeguero', 'Perforista'])
def crear_orden(request):

    if request.method == 'POST':

        data = request.POST.copy()

        if request.user.rol.nombre_rol == 'Perforista':

            data['perforista'] = request.user.id

            bodeguero = Usuario.objects.filter(
                rol__nombre_rol='Bodeguero',
                estado=True
            ).first()

            if not bodeguero:

                messages.error(
                    request,
                    'No existe un bodeguero activo para recibir la orden.'
                )

                return redirect('crear_orden')

            data['bodeguero'] = bodeguero.id

        # ====================================
        # VALIDACION DE FECHA DE LA ORDEN
        # ====================================

        fecha_orden_raw = data.get('fecha_orden')

        fecha_orden_valor = timezone.now()

        if fecha_orden_raw:

            try:

                fecha_parseada = datetime.strptime(
                    fecha_orden_raw, '%Y-%m-%dT%H:%M'
                )

                if timezone.is_naive(fecha_parseada):
                    fecha_parseada = timezone.make_aware(
                        fecha_parseada,
                        timezone.get_current_timezone()
                    )

                if fecha_parseada > timezone.now():

                    messages.error(
                        request,
                        'La fecha de la orden no puede ser una fecha futura.'
                    )

                    return redirect('crear_orden')

                fecha_orden_valor = fecha_parseada

            except ValueError:

                messages.error(
                    request,
                    'El formato de la fecha ingresada no es válido.'
                )

                return redirect('crear_orden')

        form_orden = OrdenTiroForm(data)

        if form_orden.is_valid():

            orden = form_orden.save(commit=False)

            orden.estado = 'PENDIENTE'

            # Fecha elegida por el usuario (o "ahora" si no se cambió)
            orden.fecha_orden = fecha_orden_valor

            orden.save()

            # ====================================
            # CALCULO AUTOMATICO DE MATERIALES
            # ====================================

            cantidad_tiros = orden.cantidad_tiros

            metros_mecha = float(orden.metros_mecha)

            cantidad_dinamita = cantidad_tiros

            cantidad_fulminante = cantidad_tiros

            cantidad_mecha = cantidad_tiros * metros_mecha

            cantidad_nitrato = cantidad_tiros * 5

            # ====================================
            # BUSCAR INSUMOS
            # ====================================

            dinamita = Insumo.objects.filter(
                Q(nombre_insumo__icontains='RIODIN') |
                Q(nombre_insumo__icontains='RIOGEL')
            ).first()

            fulminante = Insumo.objects.filter(
                nombre_insumo__icontains='FULMINANTE'
            ).first()

            mecha = Insumo.objects.filter(
                Q(nombre_insumo__icontains='MECHA_NEGRA') |
                Q(nombre_insumo__icontains='MECHA_BLANCA')
            ).first()

            nitrato = Insumo.objects.filter(
                Q(nombre_insumo__icontains='ANFO') |
                Q(nombre_insumo__icontains='NITRATO')
            ).first()

            # ====================================
            # GUARDAR MATERIALES DE LA ORDEN
            # ====================================

            if dinamita:

                MaterialOrden.objects.create(
                    orden_tiro=orden,
                    insumo=dinamita,
                    cantidad=cantidad_dinamita
                )

            if fulminante:

                MaterialOrden.objects.create(
                    orden_tiro=orden,
                    insumo=fulminante,
                    cantidad=cantidad_fulminante
                )

            if mecha:

                MaterialOrden.objects.create(
                    orden_tiro=orden,
                    insumo=mecha,
                    cantidad=cantidad_mecha
                )

            if nitrato:

                MaterialOrden.objects.create(
                    orden_tiro=orden,
                    insumo=nitrato,
                    cantidad=cantidad_nitrato
                )

            # ====================================
            # AUDITORIA
            # ====================================

            Auditoria.objects.create(
                usuario=request.user,
                accion='SOLICITUD DE ORDEN',
                descripcion=(
                    f'El perforista {orden.perforista.username} '
                    f'solicitó la orden {orden.codigo_orden} '
                    f'con {orden.cantidad_tiros} tiros, '
                    f'{orden.metros_mecha} metros de mecha por tiro, '
                    f'en el lugar {orden.lugar.nombre}.'
                )
            )

            messages.success(
                request,
                'Orden de tiro creada correctamente. Pendiente de revisión del bodeguero.'
            )

            if request.user.rol.nombre_rol == 'Perforista':

                return redirect('mis_ordenes_perforista')

            return redirect('ordenes')

        else:

            print(form_orden.errors)

            messages.error(
                request,
                'No se pudo crear la orden. Revisa los datos.'
            )

    else:

        form_orden = OrdenTiroForm()

    if request.user.rol.nombre_rol == 'Perforista':

        return render(
            request,
            'despachos/crear_orden_perforista.html',
            {
                'form_orden': form_orden
            }
        )

    return render(
        request,
        'despachos/crear_orden.html',
        {
            'form_orden': form_orden
        }
    )
@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def despachar_orden(request, id):
    orden = OrdenTiro.objects.get(id=id)

    if orden.estado != 'DESPACHADA':
        despacho = Despacho.objects.create(
            orden_tiro=orden,
            bodeguero=orden.bodeguero,
            estado='ENTREGADO',
            observacion='Despacho generado desde la orden de tiro.'
        )

        detalles_orden = DetalleOrdenTiro.objects.filter(orden_tiro=orden)

        for detalle in detalles_orden:
            DetalleDespacho.objects.create(
                despacho=despacho,
                insumo=detalle.insumo,
                cantidad=detalle.cantidad
            )

        orden.estado = 'DESPACHADA'
        orden.save()

    return redirect('ordenes')
@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def lista_despachos(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    despachos = Despacho.objects.all().order_by('-fecha_despacho')

    if fecha_inicio:
        despachos = despachos.filter(fecha_despacho__date__gte=fecha_inicio)

    if fecha_fin:
        despachos = despachos.filter(fecha_despacho__date__lte=fecha_fin)

    paginator = Paginator(despachos, 10)
    page_number = request.GET.get('page')
    despachos = paginator.get_page(page_number)

    return render(request, 'despachos/lista_despachos.html', {
        'despachos': despachos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'page_obj': despachos
    })
@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def detalle_despacho(request, id):

    despacho = Despacho.objects.get(id=id)

    detalles = DetalleDespacho.objects.filter(
        despacho=despacho
    )

    return render(
        request,
        'despachos/detalle_despacho.html',
        {
            'despacho': despacho,
            'detalles': detalles
        }
    )

@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def comprobante_despacho_pdf(request, id):

    despacho = Despacho.objects.get(id=id)

    detalles = DetalleDespacho.objects.filter(
        despacho=despacho
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="comprobante_despacho_'
        f'{despacho.orden_tiro.codigo_orden}.pdf"'
    )

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    def encabezado():

        logo_path = os.path.join(
            settings.BASE_DIR,
            'static',
            'img',
            'logo_ecuaminerales.jpeg'
        )

        if os.path.exists(logo_path):
            p.drawImage(
                logo_path,
                40,
                height - 90,
                width=75,
                height=55,
                preserveAspectRatio=True,
                mask='auto'
            )

        p.setFillColor(colors.HexColor('#243b80'))
        p.setFont('Helvetica-Bold', 22)

        p.drawCentredString(
            width / 2,
            height - 45,
            'ECUAMINERALES S.A.'
        )

        p.setFillColor(colors.black)
        p.setFont('Helvetica-Bold', 15)

        p.drawCentredString(
            width / 2,
            height - 70,
            'Comprobante de Despacho'
        )

        p.setFillColor(colors.HexColor('#555555'))
        p.setFont('Helvetica-Oblique', 9)

        p.drawCentredString(
            width / 2,
            height - 88,
            'Sistema de Control de Explosivos e Inventario'
        )

        p.setFillColor(colors.black)
        p.setFont('Helvetica', 9)

        p.drawString(
            40,
            height - 115,
            f'Generado por: {request.user.username}'
        )

        p.drawRightString(
            width - 40,
            height - 115,
            f'Fecha emisión: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
        )

        p.setStrokeColor(colors.HexColor('#243b80'))
        p.setLineWidth(1)
        p.line(40, height - 130, width - 40, height - 130)

    def pie_pagina():

        p.setFont('Helvetica', 8)
        p.setFillColor(colors.grey)

        p.drawString(
            40,
            40,
            'ECUMINERALES S.A. - Sistema de control de explosivos e inventario'
        )

        p.drawRightString(
            width - 40,
            40,
            f'Página {p.getPageNumber()}'
        )

    encabezado()

    y = height - 165

    p.setFillColor(colors.HexColor('#f2f4f8'))
    p.roundRect(40, y - 95, width - 80, 105, 6, fill=True, stroke=False)

    p.setFillColor(colors.HexColor('#243b80'))
    p.setFont('Helvetica-Bold', 11)
    p.drawString(55, y - 10, 'Datos del despacho')

    p.setFillColor(colors.black)
    p.setFont('Helvetica-Bold', 9)

    p.drawString(55, y - 35, 'Orden:')
    p.drawString(55, y - 55, 'Fecha despacho:')
    p.drawString(55, y - 75, 'Bodeguero:')
    p.drawString(320, y - 35, 'Estado:')

    p.setFont('Helvetica', 9)

    p.drawString(150, y - 35, str(despacho.orden_tiro.codigo_orden))
    p.drawString(
        150,
        y - 55,
        despacho.fecha_despacho.strftime('%d/%m/%Y %H:%M')
    )
    p.drawString(150, y - 75, str(despacho.bodeguero.username))

    estado = str(despacho.estado)

    if estado == 'ENTREGADO':
        color_estado = '#198754'
    elif estado == 'PENDIENTE':
        color_estado = '#ffc107'
    elif estado == 'RECHAZADO':
        color_estado = '#dc3545'
    else:
        color_estado = '#6c757d'

    p.setFillColor(colors.HexColor(color_estado))
    p.roundRect(380, y - 42, 90, 16, 4, fill=True, stroke=False)

    if estado == 'PENDIENTE':
        p.setFillColor(colors.black)
    else:
        p.setFillColor(colors.white)

    p.setFont('Helvetica-Bold', 7)
    p.drawCentredString(425, y - 37, estado)

    y -= 125

    p.setFillColor(colors.HexColor('#243b80'))
    p.setFont('Helvetica-Bold', 11)
    p.drawString(40, y, 'Observación')

    y -= 20

    p.setFillColor(colors.black)
    p.setFont('Helvetica', 9)

    observacion = despacho.observacion or 'Sin observación'

    p.drawString(40, y, str(observacion)[:95])

    y -= 40

    p.setFillColor(colors.HexColor('#243b80'))
    p.setFont('Helvetica-Bold', 11)
    p.drawString(40, y, 'Materiales entregados')

    y -= 30

    p.setFillColor(colors.HexColor('#243b80'))
    p.rect(40, y - 6, width - 80, 22, fill=True, stroke=False)

    p.setFillColor(colors.white)
    p.setFont('Helvetica-Bold', 8)

    p.drawString(50, y, 'INSUMO')
    p.drawString(230, y, 'TIPO')
    p.drawString(350, y, 'CANTIDAD')
    p.drawString(445, y, 'UNIDAD')

    y -= 28

    contador = 0

    for detalle in detalles:

        if contador % 2 == 0:
            p.setFillColor(colors.HexColor('#f2f4f8'))
            p.rect(40, y - 5, width - 80, 20, fill=True, stroke=False)

        p.setFillColor(colors.black)
        p.setFont('Helvetica', 8)

        p.drawString(50, y, str(detalle.insumo.nombre_insumo)[:28])
        p.drawString(230, y, str(detalle.insumo.get_tipo_insumo_display())[:18])
        p.drawRightString(390, y, str(detalle.cantidad))
        p.drawString(445, y, str(detalle.insumo.unidad_medida)[:18])

        y -= 22
        contador += 1

        if y < 180:
            pie_pagina()
            p.showPage()
            encabezado()

            y = height - 165

            p.setFillColor(colors.HexColor('#243b80'))
            p.setFont('Helvetica-Bold', 11)
            p.drawString(40, y, 'Materiales entregados')

            y -= 30

            p.setFillColor(colors.HexColor('#243b80'))
            p.rect(40, y - 6, width - 80, 22, fill=True, stroke=False)

            p.setFillColor(colors.white)
            p.setFont('Helvetica-Bold', 8)

            p.drawString(50, y, 'INSUMO')
            p.drawString(230, y, 'TIPO')
            p.drawString(350, y, 'CANTIDAD')
            p.drawString(445, y, 'UNIDAD')

            y -= 28

    y -= 65

    if y < 120:
        pie_pagina()
        p.showPage()
        encabezado()
        y = height - 260

    p.setStrokeColor(colors.black)
    p.setLineWidth(1)

    p.line(70, y, 230, y)
    p.line(340, y, 500, y)

    p.setFont('Helvetica-Bold', 9)
    p.setFillColor(colors.black)

    p.drawCentredString(150, y - 18, 'Firma Bodeguero')
    p.drawCentredString(420, y - 18, 'Firma Receptor')

    p.setFont('Helvetica', 8)
    p.setFillColor(colors.grey)

    p.drawCentredString(150, y - 33,'')
    p.drawCentredString(420, y - 33, '')

    pie_pagina()

    p.showPage()
    p.save()

    return response

@login_required
def reporte_ordenes_pdf(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_ordenes.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    ordenes = OrdenTiro.objects.all().order_by('-fecha_orden')

    def encabezado():

        logo_path = os.path.join(
            settings.BASE_DIR,
            'static',
            'img',
            'logo_ecuaminerales.jpeg'
        )

        if os.path.exists(logo_path):
            p.drawImage(
                logo_path,
                40,
                height - 90,
                width=75,
                height=55,
                preserveAspectRatio=True,
                mask='auto'
            )

        p.setFillColor(colors.HexColor('#243b80'))
        p.setFont('Helvetica-Bold', 22)

        p.drawCentredString(
            width / 2,
            height - 45,
            'ECUMINERALES S.A.'
        )

        p.setFillColor(colors.black)
        p.setFont('Helvetica-Bold', 15)

        p.drawCentredString(
            width / 2,
            height - 70,
            'Reporte de Órdenes de Tiro'
        )

        p.setFillColor(colors.HexColor('#555555'))
        p.setFont('Helvetica-Oblique', 9)

        p.drawCentredString(
            width / 2,
            height - 88,
            'Sistema de Control de Explosivos e Inventario'
        )

        p.setFillColor(colors.black)
        p.setFont('Helvetica', 9)

        p.drawString(
            40,
            height - 115,
            f'Generado por: {request.user.username}'
        )

        p.drawRightString(
            width - 40,
            height - 115,
            f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}'
        )

        p.setStrokeColor(colors.HexColor('#243b80'))
        p.setLineWidth(1)
        p.line(40, height - 130, width - 40, height - 130)

    def cabecera_tabla(y):

        p.setFillColor(colors.HexColor('#243b80'))
        p.rect(40, y - 6, width - 80, 22, fill=True, stroke=False)

        p.setFillColor(colors.white)
        p.setFont('Helvetica-Bold', 8)

        p.drawString(45, y, 'CÓDIGO')
        p.drawString(120, y, 'FECHA')
        p.drawString(210, y, 'PERFORISTA')
        p.drawString(320, y, 'LUGAR')
        p.drawString(430, y, 'ESTADO')

        p.setFillColor(colors.black)

    def pie_pagina():

        p.setFont('Helvetica', 8)
        p.setFillColor(colors.grey)

        p.drawString(
            40,
            40,
            'ECUMINERALES S.A. - Sistema de control de explosivos e inventario'
        )

        p.drawRightString(
            width - 40,
            40,
            f'Página {p.getPageNumber()}'
        )

    encabezado()

    y = height - 165
    cabecera_tabla(y)
    y -= 28

    contador = 0

    for orden in ordenes:

        if contador % 2 == 0:
            p.setFillColor(colors.HexColor('#f2f4f8'))
            p.rect(40, y - 5, width - 80, 20, fill=True, stroke=False)

        p.setFillColor(colors.black)
        p.setFont('Helvetica', 8)

        p.drawString(45, y, str(orden.codigo_orden)[:12])
        p.drawString(120, y, orden.fecha_orden.strftime('%d/%m/%Y %H:%M'))
        p.drawString(210, y, str(orden.perforista.username)[:18])
        p.drawString(320, y, str(orden.lugar.nombre)[:18])

        estado = str(orden.estado)

        if estado == 'DESPACHADA':
            color_estado = '#198754'
        elif estado == 'RECHAZADA':
            color_estado = '#dc3545'
        elif estado == 'PENDIENTE':
            color_estado = '#ffc107'
        else:
            color_estado = '#6c757d'

        p.setFillColor(colors.HexColor(color_estado))
        p.roundRect(430, y - 4, 90, 14, 4, fill=True, stroke=False)

        if estado == 'PENDIENTE':
            p.setFillColor(colors.black)
        else:
            p.setFillColor(colors.white)

        p.setFont('Helvetica-Bold', 7)
        p.drawCentredString(475, y, estado)

        y -= 22
        contador += 1

        if y < 80:

            pie_pagina()
            p.showPage()

            encabezado()

            y = height - 165
            cabecera_tabla(y)
            y -= 28

    pie_pagina()

    p.showPage()
    p.save()

    return response


COLOR_AZUL_MARCA = colors.HexColor('#243b80')   # color corporativo ya usado en tu sistema
COLOR_GRIS_GRUPO = colors.HexColor('#d9d9d9')   # FULMINANTE 
COLOR_CREMA_GRUPO = colors.HexColor('#fdebd0')  # DINAMITA
COLOR_VERDE_GRUPO = colors.HexColor('#d9ead3')  # MECHA LENTA
COLOR_NARANJA_SALDO = colors.HexColor('#f5a623')  # columna SALDO destacada
COLOR_GRIS_CLARO_LABEL = colors.HexColor('#f2f2f2')

DIAS_SEMANA = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']


TIPO_MOVIMIENTO_ENTRADA = 'ENTRADA'


PRODUCTOS_EXPLOSIVOS = [
    {'nombre_insumo': 'FULMINANTE', 'nombre': 'FULMINANTE', 'color': COLOR_GRIS_GRUPO},
    {'nombre_insumo': 'EMULNOR', 'nombre': 'EMULNOR', 'color': COLOR_CREMA_GRUPO},
    {'nombre_insumo': 'MECHA_NEGRA', 'nombre': 'MECHA_NEGRA', 'color': COLOR_VERDE_GRUPO},
]

MOVIMIENTOS_POR_DIA = 7  



def obtener_datos_producto_dia(producto_nombre_insumo, fecha_dia):
    """
    Devuelve los movimientos del día `fecha_dia` para el insumo cuyo
    `nombre_insumo` coincide con `producto_nombre_insumo`, en la forma
    que espera la tabla del reporte.
    """
    movimientos_qs = MovimientoInventario.objects.filter(
        insumo__nombre_insumo__iexact=producto_nombre_insumo,
        fecha_movimiento__date=fecha_dia,
    ).order_by('fecha_movimiento')[:MOVIMIENTOS_POR_DIA]

    movimientos = []
    saldo_final = None
    egreso_total = Decimal('0')
    ingreso_total = Decimal('0')
    saldo_inicial = None

    for indice, mov in enumerate(movimientos_qs):
        if indice == 0:
            saldo_inicial = mov.stock_anterior

        if mov.tipo_movimiento == TIPO_MOVIMIENTO_ENTRADA:
            movimientos.append({'egreso': None, 'ingreso': mov.cantidad, 'saldo': mov.stock_actual})
            ingreso_total += mov.cantidad or Decimal('0')
        else:
            movimientos.append({'egreso': mov.cantidad, 'ingreso': None, 'saldo': mov.stock_actual})
            egreso_total += mov.cantidad or Decimal('0')

        saldo_final = mov.stock_actual

    # Completar con filas en blanco hasta MOVIMIENTOS_POR_DIA (igual que
    # el formato en papel, que siempre muestra 6 líneas aunque sobren).
    while len(movimientos) < MOVIMIENTOS_POR_DIA:
        movimientos.append({'egreso': None, 'ingreso': None, 'saldo': None})

    return {
        'saldo_inicial': saldo_inicial,
        'movimientos': movimientos,
        'egreso_total': egreso_total if egreso_total else None,
        'ingreso_total': ingreso_total if ingreso_total else None,
        'saldo_final': saldo_final,
    }


def obtener_saldo_inicial_semana(producto_nombre_insumo, lunes_de_la_semana):
    """
    Saldo con el que arranca la semana: el `stock_actual` del último
    movimiento anterior al lunes de esa semana. Si no hay movimientos
    previos, usa el `stock_anterior` del primer movimiento de la semana.
    """
    ultimo_anterior = MovimientoInventario.objects.filter(
        insumo__nombre_insumo__iexact=producto_nombre_insumo,
        fecha_movimiento__date__lt=lunes_de_la_semana,
    ).order_by('-fecha_movimiento').first()

    if ultimo_anterior:
        return ultimo_anterior.stock_actual

    primero_semana = MovimientoInventario.objects.filter(
        insumo__nombre_insumo__iexact=producto_nombre_insumo,
        fecha_movimiento__date__gte=lunes_de_la_semana,
    ).order_by('fecha_movimiento').first()

    return primero_semana.stock_anterior if primero_semana else None


def _fmt(valor):
    """Formatea un valor numérico o deja la celda en blanco si es None."""
    if valor is None:
        return ''
    return f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _lunes_de_la_semana(fecha_referencia):
    """Devuelve el lunes de la semana ISO que contiene fecha_referencia."""
    return fecha_referencia - timedelta(days=fecha_referencia.weekday())


# ---------------------------------------------------------------------
# VISTA PRINCIPAL
# ---------------------------------------------------------------------

@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def reporte_despachos_pdf(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_despachos.pdf"'

    # TODO(CONEXIÓN DE DATOS): decide si la semana se recibe por GET
    # (?fecha=2026-09-07) o siempre es la semana actual.
    fecha_param = request.GET.get('fecha')
    if fecha_param:
        try:
            fecha_referencia = datetime.strptime(fecha_param, '%Y-%m-%d').date()
        except ValueError:
            fecha_referencia = timezone.localtime(timezone.now()).date()
    else:
        fecha_referencia = timezone.localtime(timezone.now()).date()

    lunes = _lunes_de_la_semana(fecha_referencia)
    fechas_semana = [lunes + timedelta(days=i) for i in range(7)]

   
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=20,
        rightMargin=20,
        topMargin=24,
        bottomMargin=24,
    )

    ancho_total = letter[0] - doc.leftMargin - doc.rightMargin

    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        'TituloReporte',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        fontSize=15,
        spaceAfter=6,
    )

    estilo_celda = ParagraphStyle(
        'CeldaTabla',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.6,
        alignment=TA_CENTER,
        leading=7.8,
    )

    estilo_celda_bold = ParagraphStyle(
        'CeldaTablaBold',
        parent=estilo_celda,
        fontName='Helvetica-Bold',
    )

    estilo_numero_fila = ParagraphStyle(
        'NumeroFila',
        parent=estilo_celda,
        fontSize=6.6,
    )

    estilo_label_dia = ParagraphStyle(
        'LabelDia',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.2,
        alignment=TA_LEFT,
        leading=8.4,
    )

    elementos = []

    elementos.append(Paragraph('CONTROL SEMANAL DE EXPLOSIVOS', estilo_titulo))

    # --- Construcción de la matriz de la tabla ---

    n_grupos = len(PRODUCTOS_EXPLOSIVOS)
    n_columnas = 1 + n_grupos * 3  # 1 columna de etiqueta + 3 subcolumnas por producto

    col_label_w = 42  # suficiente para "CONSUMO SEMANAL" en 2 líneas
    col_dato_w = (ancho_total - col_label_w) / (n_grupos * 3)
    anchos_columnas = [col_label_w] + [col_dato_w] * (n_grupos * 3)

    data = []
    estilos_tabla = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.3),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]

    # Fila 0: nombre de cada producto (spanning 3 columnas)
    fila0 = ['']
    for producto in PRODUCTOS_EXPLOSIVOS:
        fila0 += [Paragraph(producto['nombre'], estilo_celda_bold), '', '']
    data.append(fila0)

    col_inicio = 1
    for producto in PRODUCTOS_EXPLOSIVOS:
        col_fin = col_inicio + 2
        estilos_tabla.append(('SPAN', (col_inicio, 0), (col_fin, 0)))
        estilos_tabla.append(('BACKGROUND', (col_inicio, 0), (col_fin, 0), producto['color']))
        col_inicio = col_fin + 1

    # Fila 1: EGRESO / INGRESO / SALDO por producto
    fila1 = ['']
    for _ in PRODUCTOS_EXPLOSIVOS:
        fila1 += [
            Paragraph('EGRESO', estilo_celda_bold),
            Paragraph('INGRESO', estilo_celda_bold),
            Paragraph('SALDO', estilo_celda_bold),
        ]
    data.append(fila1)

    col_inicio = 1
    for producto in PRODUCTOS_EXPLOSIVOS:
        estilos_tabla.append(('BACKGROUND', (col_inicio, 1), (col_inicio + 1, 1), producto['color']))
        estilos_tabla.append(('BACKGROUND', (col_inicio + 2, 1), (col_inicio + 2, 1), COLOR_NARANJA_SALDO))
        col_inicio += 3

    fila_header_repetir = 2  # filas 0 y 1 se repiten en cada página

    # Acumuladores para el resumen final (SALDOS / CONSUMO SEMANAL),
    # se van llenando a medida que recorremos los 7 días.
    acumulado_semana = {
        producto['nombre_insumo']: {
            'egreso_total': Decimal('0'),
            'ingreso_total': Decimal('0'),
            'saldo_final': None,
        }
        for producto in PRODUCTOS_EXPLOSIVOS
    }

    # Fila 2: saldo inicial general de la semana (sin número de fila,
    # igual que en el PDF de referencia)
    fila2 = ['']
    for producto in PRODUCTOS_EXPLOSIVOS:
        saldo_inicial_semana = obtener_saldo_inicial_semana(producto['nombre_insumo'], lunes)
        acumulado_semana[producto['nombre_insumo']]['saldo_final'] = saldo_inicial_semana
        fila2 += [
            Paragraph('', estilo_celda),
            Paragraph('', estilo_celda),
            Paragraph(_fmt(saldo_inicial_semana), estilo_celda_bold),
        ]
    data.append(fila2)
    fila_actual = 2

    col_inicio = 1
    for producto in PRODUCTOS_EXPLOSIVOS:
        estilos_tabla.append(('BACKGROUND', (col_inicio, fila_actual), (col_inicio + 1, fila_actual), producto['color']))
        estilos_tabla.append(('BACKGROUND', (col_inicio + 2, fila_actual), (col_inicio + 2, fila_actual), COLOR_NARANJA_SALDO))
        col_inicio += 3
      
    # --- Bloques por día ---
    for dia_nombre, fecha_dia in zip(DIAS_SEMANA, fechas_semana):

        fila_actual += 1
        data.append([
            Paragraph(
                f' &nbsp;&nbsp;&nbsp;&nbsp;<b>FECHA:</b> {dia_nombre} '
                f'({fecha_dia.strftime("%d/%m/%Y")})',
                estilo_label_dia
            )
        ] + [''] * (n_columnas - 1))
        estilos_tabla.append(('SPAN', (0, fila_actual), (-1, fila_actual)))
        estilos_tabla.append(('BACKGROUND', (0, fila_actual), (-1, fila_actual), COLOR_GRIS_CLARO_LABEL))

        datos_por_producto = {
            producto['nombre_insumo']: obtener_datos_producto_dia(producto['nombre_insumo'], fecha_dia)
            for producto in PRODUCTOS_EXPLOSIVOS
        }

        # Acumular totales del día en el resumen semanal
        for producto in PRODUCTOS_EXPLOSIVOS:
            datos_dia = datos_por_producto[producto['nombre_insumo']]
            acumulado = acumulado_semana[producto['nombre_insumo']]
            acumulado['egreso_total'] += datos_dia['egreso_total'] or Decimal('0')
            acumulado['ingreso_total'] += datos_dia['ingreso_total'] or Decimal('0')
            if datos_dia['saldo_final'] is not None:
                acumulado['saldo_final'] = datos_dia['saldo_final']

        for i in range(MOVIMIENTOS_POR_DIA):
            fila_actual += 1
            fila = [Paragraph(str(i + 1), estilo_numero_fila)]
            for producto in PRODUCTOS_EXPLOSIVOS:
                mov = datos_por_producto[producto['nombre_insumo']]['movimientos'][i]
                fila += [
                    Paragraph(_fmt(mov['egreso']), estilo_celda),
                    Paragraph(_fmt(mov['ingreso']), estilo_celda),
                    Paragraph(_fmt(mov['saldo']), estilo_celda),
                ]
            data.append(fila)

            col_inicio = 1
            for producto in PRODUCTOS_EXPLOSIVOS:
                estilos_tabla.append((
                    'BACKGROUND',
                    (col_inicio, fila_actual), (col_inicio + 2, fila_actual),
                    producto['color']
                ))
                col_inicio += 3
    # --- Fila en blanco después del domingo ---
    fila_actual += 1
    fila_blanco = fila_actual
    data.append([''] * n_columnas)
    estilos_tabla.extend([
    ('LINEABOVE', (0, fila_blanco), (-1, fila_blanco), 0, colors.black),
    ('LINEBELOW', (0, fila_blanco), (-1, fila_blanco), 0, colors.black),
    ('LINEBEFORE', (0, fila_blanco), (-1, fila_blanco), 0, colors.white),
    ('LINEAFTER', (0, fila_blanco), (-1, fila_blanco), 0, colors.white),
    ('INNERGRID', (0, fila_blanco), (-1, fila_blanco), 0, colors.white),
    ])
    # --- Fila única: SALDOS + Productos + Valores ---
    fila_actual += 1

    fila_saldos = [Paragraph('SALDOS', estilo_celda_bold)]

    for producto in PRODUCTOS_EXPLOSIVOS:
     acumulado = acumulado_semana[producto['nombre_insumo']]
     fila_saldos += [
        Paragraph(producto['nombre'], estilo_celda_bold),  # ocupa 2 columnas
        '',
        Paragraph(_fmt(acumulado['saldo_final']), estilo_celda_bold)  # celda naranja
    ]

    data.append(fila_saldos)

    # Mantener el mismo estilo del encabezado original
    col_inicio = 1
    for producto in PRODUCTOS_EXPLOSIVOS:
     estilos_tabla.append(('SPAN', (col_inicio, fila_actual), (col_inicio + 1, fila_actual)))
     estilos_tabla.append(('BACKGROUND', (col_inicio, fila_actual), (col_inicio + 1, fila_actual), producto['color']))
     estilos_tabla.append(('BACKGROUND', (col_inicio + 2, fila_actual), (col_inicio + 2, fila_actual), COLOR_NARANJA_SALDO))
     col_inicio += 3

    fila_actual += 1
    fila_consumo = [Paragraph('CONSUMO SEMANAL', estilo_celda_bold)]
    for producto in PRODUCTOS_EXPLOSIVOS:
        acumulado = acumulado_semana[producto['nombre_insumo']]
        fila_consumo += [
            Paragraph(_fmt(acumulado['egreso_total'] or None), estilo_celda),
            Paragraph(_fmt(acumulado['ingreso_total'] or None), estilo_celda),
            Paragraph('', estilo_celda),
        ]
    data.append(fila_consumo)

    tabla = Table(
        data,
        colWidths=anchos_columnas,
        repeatRows=fila_header_repetir,
    )
    tabla.setStyle(TableStyle(estilos_tabla))

    elementos.append(tabla)

    # --- Pie de página (numeración) ---
    def pie_pagina(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawRightString(
            letter[0] - doc_obj.rightMargin, 12,
            f'Página {doc_obj.page}'
        )
        canvas_obj.restoreState()

    doc.build(elementos, onFirstPage=pie_pagina, onLaterPages=pie_pagina)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    response.write(pdf_bytes)

    return response

@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def ordenes_bodeguero(request):

    ordenes = OrdenTiro.objects.filter(
        estado='PENDIENTE'
    ).order_by('-fecha_orden')

    ordenes_materiales = []

    for orden in ordenes:
        materiales = calcular_materiales(orden.cantidad_tiros)

        ordenes_materiales.append({
            'orden': orden,
            'materiales': materiales
        })

    return render(request, 'despachos/ordenes_bodeguero.html', {
        'ordenes_materiales': ordenes_materiales
    })


@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def historial_bodeguero(request):

    if request.user.rol.nombre_rol == 'Administrador':
        despachos = Despacho.objects.all().order_by('-fecha_despacho')
    else:
        despachos = Despacho.objects.filter(
            bodeguero=request.user
        ).order_by('-fecha_despacho')

    return render(request, 'despachos/historial_bodeguero.html', {
        'despachos': despachos
    })
@login_required
@rol_requerido(['Administrador', 'Perforista'])
def panel_perforista(request):

    ordenes = OrdenTiro.objects.filter(
        perforista=request.user
    ).order_by('-fecha_orden')

    total_ordenes = ordenes.count()
    pendientes = ordenes.filter(estado='PENDIENTE').count()
    despachadas = ordenes.filter(estado='DESPACHADA').count()
    rechazadas = ordenes.filter(estado='RECHAZADA').count()

    ultimas_ordenes = ordenes[:5]

    return render(request, 'despachos/panel_perforista.html', {
        'total_ordenes': total_ordenes,
        'pendientes': pendientes,
        'despachadas': despachadas,
        'rechazadas': rechazadas,
        'ultimas_ordenes': ultimas_ordenes
    })
@login_required
@rol_requerido(['Administrador', 'Perforista'])
def mis_ordenes_perforista(request):

    ordenes = OrdenTiro.objects.filter(
        perforista=request.user
    ).order_by('-fecha_orden')

    paginator = Paginator(ordenes, 10)
    page_number = request.GET.get('page')
    ordenes = paginator.get_page(page_number)

    return render(request, 'despachos/mis_ordenes_perforista.html', {
        'ordenes': ordenes,
        'page_obj': ordenes
    })
@login_required
@rol_requerido(['Administrador', 'Bodeguero'])

@login_required
def editar_materiales(request, orden_id):

    orden = get_object_or_404(
        OrdenTiro,
        id=orden_id
    )

    materiales = MaterialOrden.objects.filter(
        orden_tiro=orden
    )

    if request.method == 'POST':

        for material in materiales:

            nueva_cantidad = request.POST.get(
                f'material_{material.id}'
            )

            nuevo_insumo = request.POST.get(
                f'insumo_{material.id}'
            )

            if nueva_cantidad:
                material.cantidad = nueva_cantidad

            if nuevo_insumo:
                material.insumo_id = nuevo_insumo

            material.save()

        messages.success(
            request,
            'Materiales actualizados correctamente.'
        )

        return redirect('panel_bodeguero')

    return render(
        request,
        'despachos/editar_materiales.html',
        {
            'orden': orden,
            'materiales': materiales,
            'insumos': Insumo.objects.all()
        }
    )
    
    import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST


from inventario.models import MovimientoInventario

@login_required
@require_POST
def editar_fecha_despacho_ajax(request, despacho_id):
    try:
        despacho = get_object_or_404(Despacho, id=despacho_id)
        data = json.loads(request.body)
        fecha = parse_datetime(data.get('fecha_despacho'))

        if not fecha:
            return JsonResponse({'success': False, 'error': 'Fecha inválida'})

        if timezone.is_naive(fecha):
            fecha = timezone.make_aware(fecha, timezone.get_current_timezone())

        despacho.fecha_despacho = fecha
        despacho.save()

        # PROPAGAR LA FECHA A LOS MOVIMIENTOS VINCULADOS
        MovimientoInventario.objects.filter(despacho=despacho).update(
            fecha_movimiento=fecha
        )

        return JsonResponse({
            'success': True,
            'fecha_formateada': timezone.localtime(fecha).strftime('%d/%m/%Y %H:%M')
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})