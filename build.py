import os
import shutil
import subprocess

print("=" * 60)
print("      GENERADOR DE ECUAMINERALES")
print("=" * 60)

# ---------------------------------
# Eliminar compilaciones anteriores
# ---------------------------------

for carpeta in ["build", "dist"]:

    if os.path.exists(carpeta):
        shutil.rmtree(carpeta)

for archivo in ["desktop.spec", "launcher.spec"]:

    if os.path.exists(archivo):
        os.remove(archivo)

# ---------------------------------
# Compilar launcher
# ---------------------------------

print("\nCompilando Launcher...")

subprocess.run([
    "pyinstaller",
    "--onefile",
    "--windowed",
    "launcher.py"
])

# ---------------------------------
# Compilar desktop
# ---------------------------------

print("\nCompilando Desktop...")

subprocess.run([
    "pyinstaller",
    "--onefile",
    "--windowed",
    "desktop.py"
])

print("\nCopiando archivos...")

# ---------------------------------
# Copiar archivos necesarios
# ---------------------------------

archivos = [

    "launcher_config.json",

    "db.sqlite3",

    ".env"

]

for archivo in archivos:

    if os.path.exists(archivo):

        shutil.copy(
            archivo,
            "dist"
        )

# ---------------------------------
# Copiar carpetas
# ---------------------------------

carpetas = [

    "static",

    "templates",

    "media"

]

for carpeta in carpetas:

    if os.path.exists(carpeta):

        destino = os.path.join(
            "dist",
            carpeta
        )

        shutil.copytree(
            carpeta,
            destino,
            dirs_exist_ok=True
        )

print("\nProceso finalizado correctamente.")
print("La carpeta DIST ya está lista.")