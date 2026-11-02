"""
GENERADOR DE EJECUTABLES - ECUAMINERALES S.A.
Uso: python build.py   (con el venv activo, desde la raíz del proyecto)
"""
import os
import shutil
import subprocess
import sys

print("=" * 60)
print("      GENERADOR DE ECUAMINERALES")
print("=" * 60)


# ─────────────────────────────────────────────
# Limpiar compilaciones anteriores
# ─────────────────────────────────────────────

for carpeta in ["build", "dist"]:
    if os.path.exists(carpeta):
        shutil.rmtree(carpeta)
        print(f"  Eliminado: {carpeta}/")

for archivo in ["desktop.spec", "launcher.spec", "server.spec",
                "ECUMINERALES.spec", "ECUMINERALES_DESKTOP.spec",
                "ECUMINERALES_LAUNCHER.spec", "ECUMINERALES_SERVER.spec"]:
    if os.path.exists(archivo):
        os.remove(archivo)


# ─────────────────────────────────────────────
# Helper de compilación
# ─────────────────────────────────────────────

def compilar(script, nombre, consola=False):
    print(f"\n[BUILD] Compilando {script} → {nombre}.exe ...")
    args = [
        "pyinstaller",
        "--onefile",
        "--icon=logo.ico",
        f"--name={nombre}",
    ]
    if not consola:
        args.append("--windowed")   # sin ventana de consola
    else:
        args.append("--console")    # con consola (server necesita mostrar logs)

    args.append(script)
    resultado = subprocess.run(args)
    if resultado.returncode != 0:
        print(f"  ERROR al compilar {script}. Revisa los mensajes anteriores.")
        sys.exit(1)
    print(f"  OK → dist/{nombre}.exe")


# ─────────────────────────────────────────────
# 1) Launcher  (ventana Tkinter + QR)
# ─────────────────────────────────────────────
compilar("launcher.py", "ECUMINERALES_LAUNCHER", consola=False)

# ─────────────────────────────────────────────
# 2) Desktop   (app de escritorio PyWebView / similar)
# ─────────────────────────────────────────────
compilar("desktop.py", "ECUMINERALES_DESKTOP", consola=False)

# ─────────────────────────────────────────────
# 3) Server    (Django + Waitress — necesita consola para ver logs)
# ─────────────────────────────────────────────
compilar("server.py", "ECUMINERALES_SERVER", consola=True)


# ─────────────────────────────────────────────
# Copiar archivos de datos a dist/
# ─────────────────────────────────────────────

print("\n[COPY] Copiando archivos de datos...")

archivos = [
    "launcher_config.json",
    "db.sqlite3",
    ".env",
]

for archivo in archivos:
    if os.path.exists(archivo):
        shutil.copy(archivo, "dist")
        print(f"  Copiado: {archivo}")
    else:
        print(f"  Omitido (no existe): {archivo}")

# ─────────────────────────────────────────────
# Copiar carpetas a dist/
# ─────────────────────────────────────────────

print("\n[COPY] Copiando carpetas...")

carpetas = [
    "static",
    "staticfiles",   # generado por collectstatic
    "templates",
    "media",
    "publico",       # módulo público (nuevo)
]

for carpeta in carpetas:
    if os.path.exists(carpeta):
        destino = os.path.join("dist", carpeta)
        shutil.copytree(carpeta, destino, dirs_exist_ok=True)
        print(f"  Copiada: {carpeta}/")
    else:
        print(f"  Omitida (no existe): {carpeta}/")


# ─────────────────────────────────────────────
# Resumen final
# ─────────────────────────────────────────────

print()
print("=" * 60)
print("  PROCESO FINALIZADO")
print("=" * 60)
print()
print("  Ejecutables generados en dist/:")
for exe in ["ECUMINERALES_LAUNCHER.exe",
            "ECUMINERALES_DESKTOP.exe",
            "ECUMINERALES_SERVER.exe"]:
    ruta = os.path.join("dist", exe)
    if os.path.exists(ruta):
        tam = os.path.getsize(ruta) // (1024 * 1024)
        print(f"    OK  {exe}  ({tam} MB)")
    else:
        print(f"    --  {exe}  (no generado)")

print()
print("  Orden de uso en la otra PC:")
print("    1. Doble clic en ECUMINERALES_SERVER.exe   ← arranca Django")
print("    2. Doble clic en ECUMINERALES_LAUNCHER.exe ← muestra QR y acceso")
print("    3. Doble clic en ECUMINERALES_DESKTOP.exe  ← abre el sistema")
print()
print("  Copia TODA la carpeta dist/ a la otra PC.")
print("=" * 60)