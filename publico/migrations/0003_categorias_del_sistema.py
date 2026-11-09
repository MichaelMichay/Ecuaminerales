import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ('publico', '0002_categorias_productos'),
    ('inventario', '0006_movimientoinventario_despacho'),
]

    operations = [
        migrations.DeleteModel(name='Producto'),
        migrations.DeleteModel(name='Categoria'),
        migrations.CreateModel(
            name='AjusteCategoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visible', models.BooleanField(default=True, help_text='Desmárcala para ocultar esta categoría al público.', verbose_name='visible en la página pública')),
                ('descripcion_publica', models.CharField(blank=True, help_text='Opcional. Texto corto bajo el nombre. No uses datos internos.', max_length=120, verbose_name='texto público')),
                ('color', models.CharField(blank=True, help_text='Opcional. Si lo dejas vacío se asigna automáticamente.', max_length=7, validators=[django.core.validators.RegexValidator('^#[0-9A-Fa-f]{6}$', 'Usa un color hexadecimal, por ejemplo #28307C.')], verbose_name='color')),
                ('orden', models.PositiveSmallIntegerField(default=100, help_text='Número menor aparece primero.', verbose_name='orden')),
                ('categoria', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ajuste_publico', to='inventario.categoriainsumo', verbose_name='categoría')),
            ],
            options={
                'verbose_name': 'ajuste de categoría',
                'verbose_name_plural': 'ajustes de categorías',
                'ordering': ['orden'],
            },
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='nombre')),
                ('descripcion', models.CharField(max_length=200, verbose_name='descripción')),
                ('orden', models.PositiveSmallIntegerField(default=0, verbose_name='orden')),
                ('activo', models.BooleanField(default=True, verbose_name='activo')),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productos_publicos', to='inventario.categoriainsumo', verbose_name='categoría')),
            ],
            options={
                'verbose_name': 'producto',
                'verbose_name_plural': 'productos',
                'ordering': ['categoria__nombre_categoria', 'orden', 'nombre'],
            },
        ),
    ]