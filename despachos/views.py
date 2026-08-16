from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import OrdenTiro, DetalleOrdenTiro, Despacho, DetalleDespacho
from inventario.models import Insumo, MovimientoInventario
from django.contrib import messages
from .forms import OrdenTiroForm, DetalleOrdenTiroForm
from usuarios.decorators import rol_requerido
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.core.paginator import Paginator
from reportes.models import Notificacion, Auditoria  
from usuarios.models import Usuario
from reportlab.lib import colors
from django.conf import settings
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import MaterialOrden
from .forms import MaterialOrdenForm
from inventario.models import Insumo
from django.db.models import Q
from .models import MaterialOrden
from inventario.models import Insumo
from django.shortcuts import render, redirect
from django.shortcuts import render, redirect, get_object_or_404

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
            usuario=request.user
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

    # CREAR DESPACHO

    despacho = Despacho.objects.create(
        orden_tiro=orden,
        bodeguero=request.user,
        estado='ENTREGADO',
        observacion='Despacho generado automáticamente.'
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

        form_orden = OrdenTiroForm(data)

        if form_orden.is_valid():

            orden = form_orden.save(commit=False)

            orden.estado = 'PENDIENTE'

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

@login_required
@rol_requerido(['Administrador', 'Bodeguero'])
def reporte_despachos_pdf(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_despachos.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    despachos = Despacho.objects.all().order_by('-fecha_despacho')

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
            'Reporte de Despachos'
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

        p.drawString(45, y, 'FECHA')
        p.drawString(155, y, 'ORDEN')
        p.drawString(245, y, 'BODEGUERO')
        p.drawString(370, y, 'ESTADO')
        p.drawString(465, y, 'OBSERVACIÓN')

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

    for despacho in despachos:

        if contador % 2 == 0:
            p.setFillColor(colors.HexColor('#f2f4f8'))
            p.rect(40, y - 5, width - 80, 20, fill=True, stroke=False)

        p.setFillColor(colors.black)
        p.setFont('Helvetica', 8)

        p.drawString(
            45,
            y,
            despacho.fecha_despacho.strftime('%d/%m/%Y %H:%M')
        )

        p.drawString(
            155,
            y,
            str(despacho.orden_tiro.codigo_orden)[:14]
        )

        p.drawString(
            245,
            y,
            str(despacho.bodeguero.username)[:18]
        )

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
        p.roundRect(370, y - 4, 75, 14, 4, fill=True, stroke=False)

        if estado == 'PENDIENTE':
            p.setFillColor(colors.black)
        else:
            p.setFillColor(colors.white)

        p.setFont('Helvetica-Bold', 7)
        p.drawCentredString(407, y, estado)

        p.setFillColor(colors.black)
        p.setFont('Helvetica', 8)

        observacion = despacho.observacion if despacho.observacion else 'Sin observación'

        p.drawString(
            465,
            y,
            str(observacion)[:20]
        )

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