from django.db import models
from django.contrib.auth.models import AbstractUser


class Rol(models.Model):
    nombre_rol = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_rol


class Usuario(AbstractUser):
    cedula = models.CharField(max_length=10, unique=True)
    telefono = models.CharField(max_length=15)
    estado = models.BooleanField(default=True)

    rol = models.ForeignKey(
        Rol,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
     nombre_completo = f"{self.first_name} {self.last_name}".strip()

     if nombre_completo:
        return nombre_completo

     return self.username