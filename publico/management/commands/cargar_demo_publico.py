from django.core.management.base import BaseCommand

from publico.models import Categoria, Comunicado, Producto

CATEGORIAS = [
    ('Cales y carbonatos', '#28307C'),
    ('Arcillas', '#3A47A3'),
    ('Silicatos', '#5B6FC7'),
    ('Áridos', '#7F8FD6'),
    ('Zeolitas', '#9AA9E6'),
]

PRODUCTOS = [
    ('Carbonato de calcio', 'Cales y carbonatos', 'Micronizado, para pinturas, plásticos y papel.'),
    ('Cal hidratada', 'Cales y carbonatos', 'Para construcción y tratamiento de aguas.'),
    ('Caolín', 'Arcillas', 'Arcilla blanca de alta pureza para porcelanato.'),
    ('Arcilla roja', 'Arcillas', 'Para ladrillos, tejas y cerámica estructural.'),
    ('Feldespato', 'Silicatos', 'Materia prima para cerámica y vidrio.'),
    ('Sílice', 'Silicatos', 'Arena silícea lavada y clasificada.'),
    ('Grava triturada', 'Áridos', 'Piedra triturada para construcción.'),
    ('Zeolita natural', 'Zeolitas', 'Para agricultura y tratamiento de agua.'),
]


class Command(BaseCommand):
    help = 'Carga categorías y productos de ejemplo (no duplica si ya existen).'

    def handle(self, *args, **opts):
        cats = {}
        for i, (nombre, color) in enumerate(CATEGORIAS):
            cats[nombre], _ = Categoria.objects.get_or_create(
                nombre=nombre, defaults={'color': color, 'orden': i})
        nuevos = 0
        for i, (nombre, cat, desc) in enumerate(PRODUCTOS):
            _, creado = Producto.objects.get_or_create(
                nombre=nombre, categoria=cats[cat],
                defaults={'descripcion': desc, 'orden': i})
            nuevos += creado
        self.stdout.write(self.style.SUCCESS(
            'Listo: %d categorías, %d productos nuevos.' % (len(cats), nuevos)))
