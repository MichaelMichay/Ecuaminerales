from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def almacen_documentos():
    """
    Carpeta propia para los PDF, FUERA de la carpeta media. Así un documento
    oculto no se puede abrir escribiendo su dirección: solo se entrega por las
    vistas "ver" y "descargar", que comprueban que esté publicado.
    """
    return FileSystemStorage(location=Path(settings.BASE_DIR) / 'documentos')