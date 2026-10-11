"""
Aplica el modulo publico a tu proyecto Ecuaminerales.

Uso (en la raiz del proyecto, con el venv activo):
    python aplicar_publico.py

Hace: descomprime publico.zip (si esta junto a manage.py), ajusta
ecuaminerales/urls.py (con copia .bak), verifica INSTALLED_APPS,
y ejecuta check + migrate + collectstatic.
"""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

raiz = Path.cwd()


def salir(msg):
    print("\nERROR:", msg)
    sys.exit(1)


if not (raiz / "manage.py").exists():
    salir("ejecuta este script en la raiz del proyecto (donde esta manage.py).")

# 1) Copiar la app
zip_ = raiz / "publico.zip"
if zip_.exists():
    with zipfile.ZipFile(zip_) as z:
        z.extractall(raiz)
    print("[1/5] publico.zip descomprimido en", raiz)
else:
    print("[1/5] No hay publico.zip aqui; uso la carpeta publico existente.")
if not (raiz / "publico" / "models.py").exists():
    salir("no encuentro la carpeta publico (ponla junto a manage.py).")

# 2) urls.py
urls = raiz / "ecuaminerales" / "urls.py"
t = urls.read_text(encoding="utf-8")
if "publico.urls" in t:
    print("[2/5] urls.py ya incluye publico.urls; sin cambios.")
else:
    shutil.copy(urls, str(urls) + ".bak")
    t, n = re.subn(
        r"path\(\s*''\s*,\s*include\(\s*'usuarios\.urls'\s*\)\s*\)",
        "path('sistema/', include('usuarios.urls'))", t)
    t, m = re.subn(
        r"(urlpatterns\s*=\s*\[[ \t]*\r?\n)",
        r"\1    path('', include('publico.urls')),\n", t, count=1)
    if not m:
        salir("no pude ubicar urlpatterns en ecuaminerales/urls.py.")
    urls.write_text(t, encoding="utf-8")
    print("[2/5] urls.py actualizado (copia en urls.py.bak). "
          "usuarios movido a /sistema/: %s" % ("si" if n else "ya estaba"))

# 3) settings.py
st = raiz / "ecuaminerales" / "settings.py"
s = st.read_text(encoding="utf-8")
if re.search(r"['\"]publico['\"]", s):
    print("[3/5] 'publico' ya esta en INSTALLED_APPS.")
else:
    shutil.copy(st, str(st) + ".bak")
    s, k = re.subn(r"(INSTALLED_APPS\s*=\s*\[[^\]]*?)(\n\])",
                   r"\1\n    'publico',\2", s, count=1, flags=re.S)
    if not k:
        salir("agrega 'publico' a INSTALLED_APPS manualmente.")
    st.write_text(s, encoding="utf-8")
    print("[3/5] 'publico' agregado a INSTALLED_APPS (copia en settings.py.bak).")

# 4) Comandos de Django
def manage(*args):
    print("      > python manage.py", *args)
    r = subprocess.run([sys.executable, "manage.py", *args])
    if r.returncode:
        salir("fallo 'manage.py %s'. Copia el error y pasamelo." % " ".join(args))

print("[4/5] Ejecutando comandos de Django...")
manage("check")
manage("migrate")
manage("collectstatic", "--noinput")

# 5) Avisos
print("[5/5] Revisando archivos de escritorio...")
for nombre in ("launcher.py", "desktop.py", "server.py"):
    f = raiz / nombre
    if f.exists():
        for i, linea in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if re.search(r"127\.0\.0\.1|localhost|:8000|8000", linea):
                print("      %s:%d: %s" % (nombre, i, linea.strip()))

print("""
LISTO. Ahora ejecuta:  python manage.py runserver
  - http://127.0.0.1:8000/          -> pagina publica
  - http://127.0.0.1:8000/sistema/  -> tu login de siempre
  - http://127.0.0.1:8000/admin/    -> crea comunicados (Publico > Comunicados)
Si en las lineas de arriba ves una URL que abre '/', cambiala a '/sistema/'
para que la app de escritorio siga entrando al login.
""")
