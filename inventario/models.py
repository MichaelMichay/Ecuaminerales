from django.db import models
from usuarios.models import Usuario


class CategoriaInsumo(models.Model):
    nombre_categoria = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre_categoria


class Insumo(models.Model):

    TIPO_INSUMO = (
        ('DINAMITA', 'Dinamita'),
        ('FULMINANTE', 'Fulminante'),
        ('MECHA', 'Mecha'),
        ('NITRATO', 'Nitrato'),
        ('OTRO', 'Otro'),
    )

    nombre_insumo = models.CharField(max_length=150)

    tipo_insumo = models.CharField(
        max_length=20,
        choices=TIPO_INSUMO,
        default='OTRO'
    )

    descripcion = models.TextField(blank=True, null=True)
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    unidad_medida = models.CharField(max_length=50)
    nivel_peligrosidad = models.CharField(max_length=100)
    categoria = models.ForeignKey(CategoriaInsumo, on_delete=models.CASCADE)
    numero_lote = models.CharField(max_length=20, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre_insumo


class LugarConsumo(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = (
        ('ENTRADA', 'ENTRADA'),
        ('SALIDA', 'SALIDA'),
    )

    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    stock_anterior = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacion = models.TextField(blank=True, null=True)
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.insumo.nombre_insumo}"