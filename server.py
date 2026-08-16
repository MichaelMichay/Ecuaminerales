import os
from waitress import serve

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecuaminerales.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

print("=" * 60)
print("ECUAMINERALES")
print("Servidor iniciado")
print("http://127.0.0.1:8000")
print("=" * 60)

serve(
    application,
    host="127.0.0.1",
    port=8000,
    threads=8
)