from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver


class ComunicadoQuerySet(models.QuerySet):
    def visibles(self):
        """Publicados y con fecha de publicación ya alcanzada."""
        return self.filter(publicado=True,
                           fecha_publicacion__lte=timezone.localdate())


class Comunicado(models.Model):
    titulo = models.CharField('título', max_length=150)
    resumen = models.CharField(
        'resumen', max_length=220,
        help_text='Texto corto que aparece en el carrusel de la página principal.')
    contenido = models.TextField(
        'contenido completo', blank=True,
        help_text='Opcional. Se muestra al pulsar "Leer comunicado".')
    fecha_publicacion = models.DateField(
        'fecha de publicación', default=timezone.localdate,
        help_text='Si pones una fecha futura, se publicará ese día.')
    publicado = models.BooleanField('publicado', default=True)
    creado = models.DateTimeField(auto_now_add=True)

    objects = ComunicadoQuerySet.as_manager()

    class Meta:
        verbose_name = 'comunicado'
        verbose_name_plural = 'comunicados'
        ordering = ['-fecha_publicacion', '-id']

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('publico:comunicado', args=[self.pk])


class AjusteCategoria(models.Model):
    """
    Ajustes opcionales de cómo se muestra, en la página pública, una categoría
    del sistema (inventario.CategoriaInsumo). Si una categoría no tiene ajuste,
    se muestra igual, con color automático.
    """
    categoria = models.OneToOneField(
        'inventario.CategoriaInsumo', on_delete=models.CASCADE,
        related_name='ajuste_publico', verbose_name='categoría')
    visible = models.BooleanField(
        'visible en la página pública', default=True,
        help_text='Desmárcala para ocultar esta categoría al público.')
    descripcion_publica = models.CharField(
        'texto público', max_length=120, blank=True,
        help_text='Opcional. Texto corto bajo el nombre. No uses datos internos.')
    color = models.CharField(
        'color', max_length=7, blank=True,
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$',
                                   'Usa un color hexadecimal, por ejemplo #28307C.')],
        help_text='Opcional. Si lo dejas vacío se asigna automáticamente.')
    orden = models.PositiveSmallIntegerField(
        'orden', default=100, help_text='Número menor aparece primero.')
    mostrar_insumos = models.BooleanField(
        'mostrar insumos al público', default=False,
        help_text='Muestra nombre, unidad de medida y stock de los insumos activos '
                  'de esta categoría. Actívalo solo si esa información puede ser pública.')
    DETALLE_STOCK = (
        ('ESTADO', 'Solo disponibilidad (Disponible / Agotado)'),
        ('CANTIDAD', 'Cantidad exacta en stock'),
    )
    detalle_stock = models.CharField(
        'detalle del stock', max_length=10, choices=DETALLE_STOCK, default='ESTADO',
        help_text='Qué tanto del stock se muestra cuando "mostrar insumos" está activo.')
    imagen = models.ImageField(
        'imagen', upload_to='publico/categorias/', blank=True,
        help_text='Imagen de la categoría para la página pública.')
    class Meta:
        verbose_name = 'ajuste de categoría'
        verbose_name_plural = 'ajustes de categorías'
        ordering = ['orden']

    def __str__(self):
        return str(self.categoria)


class Producto(models.Model):
    """Producto o servicio para mostrar al público (texto propio, no del inventario)."""
    nombre = models.CharField('nombre', max_length=100)
    categoria = models.ForeignKey(
        'inventario.CategoriaInsumo', on_delete=models.CASCADE,
        related_name='productos_publicos', verbose_name='categoría')
    descripcion = models.CharField('descripción', max_length=200)
    orden = models.PositiveSmallIntegerField('orden', default=0)
    activo = models.BooleanField('activo', default=True)

    class Meta:
        verbose_name = 'producto'
        verbose_name_plural = 'productos'
        ordering = ['categoria__nombre_categoria', 'orden', 'nombre']

    def __str__(self):
        return self.nombre
    
class ImagenInsumo(models.Model):
    """
    Imagen pública de un insumo del inventario. Vive en este módulo para no
    tocar el modelo Insumo de tu sistema.
    """
    insumo = models.OneToOneField(
        'inventario.Insumo', on_delete=models.CASCADE,
        related_name='imagen_publica', verbose_name='insumo')
    imagen = models.ImageField('imagen', upload_to='publico/insumos/')

    class Meta:
        verbose_name = 'imagen de insumo'
        verbose_name_plural = 'imágenes de insumos'

    def __str__(self):
        return str(self.insumo)


@receiver(post_delete, sender=AjusteCategoria)
@receiver(post_delete, sender=ImagenInsumo)
def borrar_archivo_de_imagen(sender, instance, **kwargs):
    """Al borrar el registro se borra también el archivo del disco."""
    nombre = instance.imagen.name
    if nombre:
        almacen = instance.imagen.storage
        transaction.on_commit(lambda: almacen.delete(nombre))