from django.db import models

from usuarios.models import Usuario
from inventario.models import LugarConsumo


class TipoActividad(models.Model):

    nombre = models.CharField(
        max_length=100,
        unique=True
    )

    descripcion = models.TextField(
        blank=True,
        null=True
    )

    unidad = models.CharField(
        max_length=30,
        default='ACTIVIDAD'
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    activo = models.BooleanField(
        default=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.nombre} - ${self.valor}"


class RegistroActividad(models.Model):

    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('RECHAZADA', 'Rechazada'),
        ('IMPUGNADA', 'Impugnada'),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='registros_actividad'
    )

    tipo_actividad = models.ForeignKey(
        TipoActividad,
        on_delete=models.PROTECT,
        related_name='registros'
    )

    lugar = models.ForeignKey(
        LugarConsumo,
        on_delete=models.PROTECT,
        related_name='registros_actividad'
    )

    fecha = models.DateField()

    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1
    )

    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PENDIENTE'
    )

    observacion = models.TextField(
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.usuario.get_full_name()} - "
            f"{self.tipo_actividad.nombre} - "
            f"{self.fecha}"
        )



class LiquidacionMensual(models.Model):

    ESTADOS = (
        ('ABIERTA', 'Abierta'),
        ('ACEPTADA', 'Aceptada'),
        ('IMPUGNADA', 'Impugnada'),
        ('CERRADA', 'Cerrada'),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='liquidaciones'
    )

    mes = models.PositiveIntegerField()

    anio = models.PositiveIntegerField()

    total_actividades = models.PositiveIntegerField(
        default=0
    )

    total_generado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default='ABIERTA'
    )

    observacion_impugnacion = models.TextField(
        blank=True,
        null=True
    )

    fecha_aceptacion = models.DateTimeField(
        null=True,
        blank=True
    )

    fecha_impugnacion = models.DateTimeField(
        null=True,
        blank=True
    )

    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True
    )

    fecha_generacion = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('usuario', 'mes', 'anio')

    def __str__(self):
        return (
            f"{self.usuario.get_full_name()} - "
            f"{self.mes}/{self.anio}"
        )

    ESTADOS = (
        ('ABIERTA', 'Abierta'),
        ('CERRADA', 'Cerrada'),
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='liquidaciones'
    )

    mes = models.PositiveIntegerField()

    anio = models.PositiveIntegerField()

    total_actividades = models.PositiveIntegerField(
        default=0
    )

    total_generado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default='ABIERTA'
    )

    fecha_generacion = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.usuario.get_full_name()} - "
            f"{self.mes}/{self.anio}"
        )