from django.db import models
from usuarios.models import Usuario


class Auditoria(models.Model):
    accion = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.accion


class Notificacion(models.Model):
    mensaje = models.TextField()

    estado = models.BooleanField(default=False)

    fecha = models.DateTimeField(auto_now_add=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.mensaje