from django.db import models
from usuarios.models import Usuario
from despachos.models import Despacho


class EntregaPolvorin(models.Model):

    ESTADO_ENTREGA = (
        ('ENTREGADO', 'ENTREGADO'),
        ('RECHAZADO', 'RECHAZADO'),
    )

    despacho = models.OneToOneField(
        Despacho,
        on_delete=models.CASCADE
    )

    polvorinero = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )

    fecha_entrega = models.DateTimeField(auto_now_add=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_ENTREGA,
        default='ENTREGADO'
    )

    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.estado} - {self.despacho.orden_tiro.codigo_orden}"