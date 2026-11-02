"""
Panel de administración de la página pública, dentro del sistema.
Solo el rol Administrador puede entrar (igual que crear_usuario).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from inventario.models import CategoriaInsumo
from reportes.models import Auditoria
from usuarios.decorators import rol_requerido

from .forms import AjusteCategoriaForm, ComunicadoForm
from .models import AjusteCategoria, Comunicado
from inventario.models import CategoriaInsumo, Insumo
from .views import servir_pdf
from .forms import AjusteCategoriaForm, ComunicadoForm, DocumentoForm, ImagenInsumoForm
from .models import AjusteCategoria, Comunicado,Documento, ImagenInsumo

def solo_admin(vista):
    return login_required(rol_requerido(['Administrador'])(vista))


def _auditar(request, accion, descripcion):
    Auditoria.objects.create(usuario=request.user, accion=accion,
                             descripcion=descripcion)


# ------------------------------------------------------------------ comunicados
@solo_admin
def comunicados(request):
    paginator = Paginator(Comunicado.objects.all(), 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'publico/panel/comunicados.html', {
        'page_obj': page, 'hoy': timezone.localdate()})


@solo_admin
def comunicado_crear(request):
    form = ComunicadoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        c = form.save()
        _auditar(request, 'CREACIÓN DE COMUNICADO',
                 f'{request.user.username} creó el comunicado "{c.titulo}".')
        messages.success(request, 'Comunicado creado correctamente.')
        return redirect('publico_panel:comunicados')
    if request.method == 'POST':
        messages.error(request, 'No se pudo guardar. Revisa los datos.')
    return render(request, 'publico/panel/comunicado_form.html',
                  {'form': form, 'titulo': 'Nuevo comunicado'})


@solo_admin
def comunicado_editar(request, pk):
    c = get_object_or_404(Comunicado, pk=pk)
    form = ComunicadoForm(request.POST or None, instance=c)
    if request.method == 'POST' and form.is_valid():
        form.save()
        _auditar(request, 'EDICIÓN DE COMUNICADO',
                 f'{request.user.username} modificó el comunicado "{c.titulo}".')
        messages.success(request, 'Comunicado actualizado correctamente.')
        return redirect('publico_panel:comunicados')
    if request.method == 'POST':
        messages.error(request, 'No se pudo guardar. Revisa los datos.')
    return render(request, 'publico/panel/comunicado_form.html',
                  {'form': form, 'titulo': 'Editar comunicado'})


@solo_admin
@require_POST
def comunicado_eliminar(request, pk):
    c = get_object_or_404(Comunicado, pk=pk)
    titulo = c.titulo
    c.delete()
    _auditar(request, 'ELIMINACIÓN DE COMUNICADO',
             f'{request.user.username} eliminó el comunicado "{titulo}".')
    messages.success(request, 'Comunicado eliminado correctamente.')
    return redirect('publico_panel:comunicados')


# ------------------------------------------------------------------ categorías
@solo_admin
def categorias(request):
    ajustes = {a.categoria_id: a for a in AjusteCategoria.objects.all()}
    filas = []
    qs = (CategoriaInsumo.objects
          .annotate(n=Count('insumo', filter=Q(insumo__estado=True)))
          .order_by('nombre_categoria'))
    for c in qs:
        a = ajustes.get(c.pk)
        filas.append({
            'cat': c,
            'n': c.n,
            'visible': a.visible if a else True,
            'mostrar': a.mostrar_insumos if a else False,
            'modo': a.get_detalle_stock_display() if a else '',
            'imagen': a.imagen if a and a.imagen else None,
        })
    return render(request, 'publico/panel/categorias.html', {'filas': filas})

@solo_admin
def categoria_editar(request, pk):
    cat = get_object_or_404(CategoriaInsumo, pk=pk)
    ajuste = (AjusteCategoria.objects.filter(categoria=cat).first()
              or AjusteCategoria(categoria=cat))
    es_post = request.method == 'POST'
    form = AjusteCategoriaForm(request.POST if es_post else None,
                               request.FILES if es_post else None,
                               instance=ajuste)
    if request.method == 'POST' and form.is_valid():
        a = form.save()
        _auditar(request, 'AJUSTE PÁGINA PÚBLICA',
                 f'{request.user.username} ajustó la categoría "{cat.nombre_categoria}": '
                 f'visible={a.visible}, mostrar insumos={a.mostrar_insumos}, '
                 f'detalle={a.detalle_stock}, imagen={"sí" if a.imagen else "no"}.')
        messages.success(request, 'Categoría actualizada correctamente.')
        return redirect('publico_panel:categorias')
    if request.method == 'POST':
        messages.error(request, 'No se pudo guardar. Revisa los datos.')
    return render(request, 'publico/panel/categoria_form.html',
                  {'form': form, 'cat': cat})

@solo_admin
@require_POST
def categoria_alternar(request, pk, campo):
    if campo not in ('visible', 'mostrar_insumos'):
        raise Http404
    cat = get_object_or_404(CategoriaInsumo, pk=pk)
    ajuste, _ = AjusteCategoria.objects.get_or_create(categoria=cat)
    nuevo = not getattr(ajuste, campo)
    setattr(ajuste, campo, nuevo)
    ajuste.save(update_fields=[campo])
    _auditar(request, 'AJUSTE PÁGINA PÚBLICA',
             f'{request.user.username} cambió "{campo}" a {nuevo} en la categoría '
             f'"{cat.nombre_categoria}".')
    messages.success(request, 'Cambio guardado.')
    return redirect('publico_panel:categorias')

# ------------------------------------------------------------------ imágenes de insumos
@solo_admin
def insumos_imagenes(request):
    buscar = request.GET.get('buscar', '').strip()
    qs = (Insumo.objects.filter(estado=True)
          .select_related('categoria', 'imagen_publica')
          .order_by('categoria__nombre_categoria', 'nombre_insumo'))
    if buscar:
        qs = qs.filter(nombre_insumo__icontains=buscar)
    page = Paginator(qs, 12).get_page(request.GET.get('page'))
    page.object_list = list(page.object_list)

    # ¿La categoría del insumo muestra insumos al público?
    muestran = set(AjusteCategoria.objects
                   .filter(visible=True, mostrar_insumos=True)
                   .values_list('categoria_id', flat=True))
    for i in page.object_list:
        i.se_muestra = i.categoria_id in muestran
    return render(request, 'publico/panel/insumos_imagenes.html',
                  {'page_obj': page, 'buscar': buscar})


@solo_admin
def insumo_imagen(request, pk):
    insumo = get_object_or_404(Insumo.objects.select_related('categoria'),
                               pk=pk, estado=True)
    imagen = (ImagenInsumo.objects.filter(insumo=insumo).first()
              or ImagenInsumo(insumo=insumo))
    es_post = request.method == 'POST'
    form = ImagenInsumoForm(request.POST if es_post else None,
                            request.FILES if es_post else None,
                            instance=imagen)
    if request.method == 'POST' and form.is_valid():
        if not form.cleaned_data.get('imagen'):          # se pidió quitarla
            ImagenInsumo.objects.filter(pk=imagen.pk).delete()   # borra también el archivo
            _auditar(request, 'IMAGEN PÁGINA PÚBLICA',
                     f'{request.user.username} quitó la imagen del insumo '
                     f'"{insumo.nombre_insumo}".')
            messages.success(request, 'Imagen eliminada.')
        else:
            form.save()
            _auditar(request, 'IMAGEN PÁGINA PÚBLICA',
                     f'{request.user.username} actualizó la imagen del insumo '
                     f'"{insumo.nombre_insumo}".')
            messages.success(request, 'Imagen guardada correctamente.')
        return redirect('publico_panel:imagenes')
    if request.method == 'POST':
        messages.error(request, 'No se pudo guardar. Revisa la imagen.')
    return render(request, 'publico/panel/insumo_imagen_form.html',
                  {'form': form, 'insumo': insumo})

# ------------------------------------------------------------------ documentos PDF
@solo_admin
def documentos(request):
    page = Paginator(Documento.objects.all(), 10).get_page(request.GET.get('page'))
    return render(request, 'publico/panel/documentos.html', {'page_obj': page})


@solo_admin
def documento_crear(request):
    es_post = request.method == 'POST'
    form = DocumentoForm(request.POST if es_post else None,
                         request.FILES if es_post else None)
    if es_post and form.is_valid():
        d = form.save()
        _auditar(request, 'DOCUMENTO PÁGINA PÚBLICA',
                 f'{request.user.username} subió el documento "{d.titulo}".')
        messages.success(request, 'Documento guardado correctamente.')
        return redirect('publico_panel:documentos')
    if es_post:
        messages.error(request, 'No se pudo guardar. Revisa los datos.')
    return render(request, 'publico/panel/documento_form.html',
                  {'form': form, 'titulo': 'Nuevo documento'})


@solo_admin
def documento_editar(request, pk):
    d = get_object_or_404(Documento, pk=pk)
    es_post = request.method == 'POST'
    form = DocumentoForm(request.POST if es_post else None,
                         request.FILES if es_post else None, instance=d)
    if es_post and form.is_valid():
        form.save()
        _auditar(request, 'DOCUMENTO PÁGINA PÚBLICA',
                 f'{request.user.username} modificó el documento "{d.titulo}" '
                 f'(publicado={d.publicado}).')
        messages.success(request, 'Documento actualizado correctamente.')
        return redirect('publico_panel:documentos')
    if es_post:
        messages.error(request, 'No se pudo guardar. Revisa los datos.')
    return render(request, 'publico/panel/documento_form.html',
                  {'form': form, 'titulo': 'Editar documento', 'doc': d})


@solo_admin
@require_POST
def documento_eliminar(request, pk):
    d = get_object_or_404(Documento, pk=pk)
    titulo = d.titulo
    d.delete()
    _auditar(request, 'DOCUMENTO PÁGINA PÚBLICA',
             f'{request.user.username} eliminó el documento "{titulo}".')
    messages.success(request, 'Documento eliminado correctamente.')
    return redirect('publico_panel:documentos')


@solo_admin
def documento_vista(request, pk):
    """Vista previa para el administrador, aunque el documento esté oculto."""
    return servir_pdf(get_object_or_404(Documento, pk=pk), descargar=False)