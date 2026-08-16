from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from despachos.models import Despacho, DetalleDespacho
from reportes.models import Auditoria
from usuarios.decorators import rol_requerido
from .models import EntregaPolvorin
from django.http import HttpResponse
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from datetime import datetime
import os

@login_required
@rol_requerido(['Administrador', 'Polvorinero'])
def panel_polvorin(request):

    despachos_pendientes = Despacho.objects.filter(
        entregapolvorin__isnull=True
    ).order_by('-fecha_despacho')

    if request.user.rol.nombre_rol == 'Administrador':
        entregas = EntregaPolvorin.objects.all().order_by('-fecha_entrega')
    else:
        entregas = EntregaPolvorin.objects.filter(
            polvorinero=request.user
        ).order_by('-fecha_entrega')

    return render(request, 'polvorin/panel.html', {
        'despachos_pendientes': despachos_pendientes,
        'entregas': entregas,
        'total_pendientes': despachos_pendientes.count(),
        'total_entregas': entregas.count()
    })


@login_required
@rol_requerido(['Administrador', 'Polvorinero'])
def registrar_entrega_polvorin(request, id):

    despacho = Despacho.objects.get(id=id)

    if EntregaPolvorin.objects.filter(despacho=despacho).exists():
        messages.warning(request, 'Este despacho ya fue entregado.')
        return redirect('panel_polvorin')

    EntregaPolvorin.objects.create(
        despacho=despacho,
        polvorinero=request.user,
        estado='ENTREGADO',
        observacion='Entrega física registrada por el polvorinero.'
    )

    Auditoria.objects.create(
        usuario=request.user,
        accion='ENTREGA POLVORÍN',
        descripcion=f'Se registró la entrega física del despacho de la orden {despacho.orden_tiro.codigo_orden}.'
    )

    messages.success(request, 'Entrega registrada correctamente.')

    return redirect('panel_polvorin')


@login_required
@rol_requerido(['Administrador', 'Polvorinero'])
def detalle_entrega_polvorin(request, id):

    entrega = EntregaPolvorin.objects.get(id=id)

    detalles = DetalleDespacho.objects.filter(
        despacho=entrega.despacho
    )

    return render(request, 'polvorin/detalle_entrega.html', {
        'entrega': entrega,
        'detalles': detalles
    })


@login_required
@rol_requerido(['Administrador', 'Polvorinero'])
def detalle_despacho_polvorin(request, id):

    despacho = Despacho.objects.get(id=id)

    detalles = DetalleDespacho.objects.filter(
        despacho=despacho
    )

    return render(request, 'polvorin/detalle_despacho_polvorin.html', {
        'despacho': despacho,
        'detalles': detalles
    })


@login_required
@rol_requerido(['Administrador', 'Polvorinero'])
def rechazar_entrega_polvorin(request, id):

    despacho = Despacho.objects.get(id=id)

    if EntregaPolvorin.objects.filter(despacho=despacho).exists():
        messages.warning(request, 'Este despacho ya fue procesado.')
        return redirect('panel_polvorin')

    EntregaPolvorin.objects.create(
        despacho=despacho,
        polvorinero=request.user,
        estado='RECHAZADO',
        observacion='Entrega rechazada por el polvorinero.'
    )

    Auditoria.objects.create(
        usuario=request.user,
        accion='RECHAZO DE ENTREGA POLVORÍN',
        descripcion=f'Se rechazó la entrega física de la orden {despacho.orden_tiro.codigo_orden}.'
    )

    messages.warning(request, 'Entrega rechazada correctamente.')

    return redirect('panel_polvorin')
@login_required
@rol_requerido(['Administrador', 'Polvorinero'])
def historial_polvorin(request):

    if request.user.rol.nombre_rol == 'Administrador':

        entregas = EntregaPolvorin.objects.all().order_by(
            '-fecha_entrega'
        )

    else:

        entregas = EntregaPolvorin.objects.filter(
            polvorinero=request.user
        ).order_by('-fecha_entrega')

    return render(request, 'polvorin/historial.html', {
        'entregas': entregas
    })

@login_required
@rol_requerido(['Administrador', 'Polvorinero'])
def comprobante_entrega_pdf(request, id):

    entrega = EntregaPolvorin.objects.get(id=id)

    despacho = entrega.despacho

    detalles = DetalleDespacho.objects.filter(
        despacho=despacho
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="comprobante_entrega_'
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
            'ECUMINERALES S.A.'
        )

        p.setFillColor(colors.black)
        p.setFont('Helvetica-Bold', 15)

        p.drawCentredString(
            width / 2,
            height - 70,
            'Comprobante de Entrega en Polvorín'
        )

        p.setFillColor(colors.HexColor('#555555'))
        p.setFont('Helvetica-Oblique', 9)

        p.drawCentredString(
            width / 2,
            height - 88,
            'Entrega física de materiales explosivos'
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
    p.roundRect(40, y - 110, width - 80, 120, 6, fill=True, stroke=False)

    p.setFillColor(colors.HexColor('#243b80'))
    p.setFont('Helvetica-Bold', 11)
    p.drawString(55, y - 10, 'Datos de la entrega')

    p.setFillColor(colors.black)
    p.setFont('Helvetica-Bold', 9)

    p.drawString(55, y - 35, 'Orden:')
    p.drawString(55, y - 55, 'Fecha entrega:')
    p.drawString(55, y - 75, 'Polvorinero:')
    p.drawString(320, y - 35, 'Bodeguero:')
    p.drawString(320, y - 55, 'Estado:')

    p.setFont('Helvetica', 9)

    p.drawString(150, y - 35, str(despacho.orden_tiro.codigo_orden))
    p.drawString(
        150,
        y - 55,
        entrega.fecha_entrega.strftime('%d/%m/%Y %H:%M')
    )
    p.drawString(150, y - 75, str(entrega.polvorinero.username))
    p.drawString(405, y - 35, str(despacho.bodeguero.username))

    estado = str(entrega.estado)

    if estado == 'ENTREGADO':
        color_estado = '#198754'
    else:
        color_estado = '#dc3545'

    p.setFillColor(colors.HexColor(color_estado))
    p.roundRect(405, y - 62, 90, 16, 4, fill=True, stroke=False)

    p.setFillColor(colors.white)
    p.setFont('Helvetica-Bold', 7)
    p.drawCentredString(450, y - 57, estado)

    y -= 140

    p.setFillColor(colors.HexColor('#243b80'))
    p.setFont('Helvetica-Bold', 11)
    p.drawString(40, y, 'Observación')

    y -= 20

    p.setFillColor(colors.black)
    p.setFont('Helvetica', 9)

    observacion = entrega.observacion or 'Sin observación'
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

    p.drawCentredString(150, y - 18, 'Firma Polvorinero')
    p.drawCentredString(420, y - 18, 'Firma Receptor')

    p.setFont('Helvetica', 8)
    p.setFillColor(colors.grey)

    p.drawCentredString(150, y - 33, '')
    p.drawCentredString(420, y - 33, '')

    pie_pagina()

    p.showPage()
    p.save()

    return response