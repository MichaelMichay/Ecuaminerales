import os
import sys
import socket
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecuaminerales.settings")

import django
django.setup()

from django.core.wsgi import get_wsgi_application
from django.core.management import call_command
from waitress import serve
import qrcode

application = get_wsgi_application()


def obtener_ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()


def generar_qr(url):
    """Genera un PNG con el QR de la URL, y lo abre con el visor de imágenes por defecto."""
    if getattr(sys, 'frozen', False):
        carpeta = Path(sys.executable).resolve().parent
    else:
        carpeta = Path(__file__).resolve().parent

    ruta_qr = carpeta / "acceso_qr.png"

    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    imagen = qr.make_image(fill_color="black", back_color="white")
    imagen.save(ruta_qr)

    try:
        os.startfile(ruta_qr)   # abre con el visor de imágenes de Windows
    except Exception:
        pass

    return ruta_qr


def main():
    call_command('migrate', interactive=False, verbosity=0)

    ip_local = obtener_ip_local()
    puerto = 8000
    url_red = f"http://{ip_local}:{puerto}"

    ruta_qr = generar_qr(url_red)

    print("=" * 60)
    print(" ECUAMINERALES S.A. - Servidor")
    print("=" * 60)
    print(f" Esta PC:                    http://127.0.0.1:{puerto}")
    print(f" Otras PCs/celulares (LAN):  {url_red}")
    print("=" * 60)
    print(f" Código QR guardado y abierto en: {ruta_qr}")
    print(" Escanéalo desde el celular (misma red WiFi) para entrar directo.")
    print("=" * 60)
    print(" NO cierres esta ventana mientras el sistema esté en uso.")
    print("=" * 60)

    serve(application, host="0.0.0.0", port=puerto, threads=8)


if __name__ == "__main__":
    main()