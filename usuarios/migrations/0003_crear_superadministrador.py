from django.db import migrations
from django.contrib.auth.hashers import make_password


def crear_superadmin(apps, schema_editor):

    Usuario = apps.get_model('usuarios', 'Usuario')
    Rol = apps.get_model('usuarios', 'Rol')

    rol_admin, _ = Rol.objects.get_or_create(
        nombre_rol='Administrador'
    )

    if not Usuario.objects.filter(username='superadmin').exists():

        Usuario.objects.create(
            username='superadmin',
            email='admin@ecuaminerales.com',
            password=make_password('Admin123*'),
            is_superuser=True,
            is_staff=True,
            is_active=True,
            cedula='0000000000',
            telefono='0999999999',
            rol=rol_admin
        )


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_alter_usuario_rol'),
    ]

    operations = [
        migrations.RunPython(crear_superadmin),
    ]