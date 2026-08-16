from django.contrib import admin

from .models import (
    CategoriaInsumo,
    Insumo,
    LugarConsumo,
    MovimientoInventario
)

admin.site.register(CategoriaInsumo)
admin.site.register(Insumo)
admin.site.register(LugarConsumo)
admin.site.register(MovimientoInventario)