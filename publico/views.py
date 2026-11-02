from django.conf import settings
from django.shortcuts import get_object_or_404, render, resolve_url

from inventario.models import CategoriaInsumo, Insumo
from django.http import FileResponse, Http404

from .models import AjusteCategoria, Comunicado,Documento, ImagenInsumo, Producto
from django.core.files.storage import default_storage
def _ctx():
    return {'login_url': resolve_url(settings.LOGIN_URL)}


PALETA = ['#28307C', '#3A47A3', '#5B6FC7', '#7F8FD6', '#9AA9E6', '#1F5F8B', '#2F80B7']

def _catalogo():
    """
    Categorías reales del sistema (solo su nombre) más los productos públicos.
    Nunca se leen insumos, stock, lotes ni peligrosidad del inventario.
    """
    ajustes = {a.categoria_id: a for a in AjusteCategoria.objects.all()}
    filas = []
    for c in CategoriaInsumo.objects.only('id', 'nombre_categoria'):
        aj = ajustes.get(c.pk)
        if aj and not aj.visible:
            continue
        filas.append((aj.orden if aj else 100, c.nombre_categoria.lower(), c, aj))
    filas.sort(key=lambda f: (f[0], f[1]))

    categorias, ids, modo_insumos = [], set(), {}
    for i, (_, _, c, aj) in enumerate(filas):
        ids.add(c.pk)
        if aj and aj.mostrar_insumos:
            modo_insumos[c.pk] = aj.detalle_stock
        categorias.append({
            'nombre': c.nombre_categoria,
            'color': (aj.color if aj and aj.color else PALETA[i % len(PALETA)]),
            'resumen': aj.descripcion_publica if aj else '',
            'imagen': aj.imagen.url if aj and aj.imagen else '',
        })
    nombre_de = {c.pk: c.nombre_categoria for _, _, c, _ in filas}

    productos = [
        {'nombre': p.nombre, 'categoria': p.categoria.nombre_categoria,
         'descripcion': p.descripcion, 'detalle': '', 'agotado': False,
         'imagen': ''}
        for p in Producto.objects.filter(activo=True, categoria_id__in=ids)
        .select_related('categoria')
    ]

    # Insumos del inventario: SOLO de categorías con "mostrar_insumos" activo y
    # SOLO estos cuatro campos (nunca lote, peligrosidad, stock mínimo, etc.).
    if modo_insumos:
        insumos = list(Insumo.objects
                       .filter(estado=True, categoria_id__in=modo_insumos.keys())
                       .order_by('nombre_insumo')
                       .values('id', 'nombre_insumo', 'unidad_medida', 'stock',
                               'categoria_id'))
        fotos = dict(ImagenInsumo.objects
                     .filter(insumo_id__in=[i['id'] for i in insumos])
                     .values_list('insumo_id', 'imagen'))
        for ins in insumos:
            agotado = ins['stock'] <= 0
            if modo_insumos[ins['categoria_id']] == 'CANTIDAD':
                detalle = 'Stock: %s %s' % (ins['stock'], ins['unidad_medida'])
            else:
                detalle = 'Agotado' if agotado else 'Disponible'
            foto = fotos.get(ins['id'])
            productos.append({
                'nombre': ins['nombre_insumo'],
                'categoria': nombre_de[ins['categoria_id']],
                'descripcion': 'Unidad de medida: %s' % ins['unidad_medida'],
                'detalle': detalle.strip(),
                'agotado': agotado,
                'imagen': default_storage.url(foto) if foto else '',
            })

    return {'categorias': categorias, 'productos': productos}

def inicio(request):
    """Página pública e informativa. Solo lee datos del módulo público."""
    ctx = _ctx()
    ctx['comunicados'] = Comunicado.objects.visibles()[:5]
    ctx['catalogo'] = _catalogo()
    ctx['documentos'] = Documento.objects.visibles()[:12]
    return render(request, 'publico/inicio.html', ctx)


def comunicado(request, pk):
    ctx = _ctx()
    ctx['c'] = get_object_or_404(
        Comunicado.objects.visibles().select_related('documento'), pk=pk)
    return render(request, 'publico/comunicado.html', ctx)


def servir_pdf(doc, descargar):
    """Entrega el PDF: en el visor del navegador (ver) o como descarga."""
    try:
        archivo = doc.archivo.open('rb')
    except (FileNotFoundError, ValueError):
        raise Http404('El archivo no está disponible.')
    resp = FileResponse(archivo, content_type='application/pdf',
                        as_attachment=descargar, filename=doc.nombre_descarga())
    resp['X-Content-Type-Options'] = 'nosniff'
    return resp


def documento_ver(request, pk):
    doc = get_object_or_404(Documento.objects.visibles(), pk=pk)
    return servir_pdf(doc, descargar=False)


def documento_descargar(request, pk):
    doc = get_object_or_404(Documento.objects.visibles(), pk=pk)
    return servir_pdf(doc, descargar=True)