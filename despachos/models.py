from django.db import models
from usuarios.models import Usuario
from inventario.models import Insumo, LugarConsumo
import random

def generar_codigo():
    numero = random.randint(1000, 9999)
    return f'OT-{numero}'

class OrdenTiro(models.Model):

    ESTADO_ORDEN = (
        ('PENDIENTE', 'PENDIENTE'),
        ('APROBADA', 'APROBADA'),
        ('RECHAZADA', 'RECHAZADA'),
        ('DESPACHADA', 'DESPACHADA'),
    )

    codigo_orden = models.CharField(
        max_length=50,
        unique=True,
        default=generar_codigo
    )
    fecha_orden = models.DateTimeField(auto_now_add=True)
    cantidad_tiros = models.IntegerField(default=0)

    metros_mecha = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.80
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_ORDEN,
        default='PENDIENTE'
    )

    observacion = models.TextField(blank=True, null=True)
    motivo_rechazo = models.TextField(blank=True, null=True)
    perforista = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='ordenes_perforista'
    )

    bodeguero = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='ordenes_bodeguero'
    )

    lugar = models.ForeignKey(
        LugarConsumo,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.codigo_orden


class DetalleOrdenTiro(models.Model):
    orden_tiro = models.ForeignKey(
        OrdenTiro,
        on_delete=models.CASCADE
    )

    insumo = models.ForeignKey(
        Insumo,
        on_delete=models.CASCADE
    )

    cantidad = models.IntegerField()

    def __str__(self):
        return f"{self.orden_tiro.codigo_orden}"


class Despacho(models.Model):

    ESTADO_DESPACHO = (
        ('PENDIENTE', 'PENDIENTE'),
        ('ENTREGADO', 'ENTREGADO'),
    )

    fecha_despacho = models.DateTimeField(auto_now_add=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_DESPACHO
    )

    observacion = models.TextField(blank=True, null=True)

    orden_tiro = models.ForeignKey(
        OrdenTiro,
        on_delete=models.CASCADE
    )

    bodeguero = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='despachos_bodeguero'
    )

    def __str__(self):
        return f"Despacho {self.id}"


class DetalleDespacho(models.Model):

    despacho = models.ForeignKey(
        Despacho,
        on_delete=models.CASCADE
    )

    insumo = models.ForeignKey(
        Insumo,
        on_delete=models.CASCADE
    )

    cantidad = models.IntegerField()

    def __str__(self):
        return f"{self.despacho.id}"


class MaterialOrden(models.Model):

    orden_tiro = models.ForeignKey(
        'OrdenTiro',
        on_delete=models.CASCADE,
        related_name='materiales'
    )

    insumo = models.ForeignKey(
        Insumo,
        on_delete=models.CASCADE
    )

    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    observacion = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.orden_tiro.codigo_orden} - {self.insumo.nombre_insumo}"