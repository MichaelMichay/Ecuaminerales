import subprocess
import time
import json
import requests
import webview
import os
import sys
import tkinter as tk
from tkinter import messagebox

CONFIG = "launcher_config.json"

server = None


def cargar_config():
    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


config = cargar_config()
IP = config["ip"]
PUERTO = config["puerto"]
URL = f"http://{IP}:{PUERTO}"

ES_SERVIDOR_LOCAL = IP in ("127.0.0.1", "localhost")


def servidor_activo():
    try:
        requests.get(URL, timeout=2)
        return True
    except Exception:
        return False


def iniciar_servidor_si_corresponde():
    global server

    if not ES_SERVIDOR_LOCAL:
        # Esta PC es un CLIENTE: nunca debe intentar levantar un servidor propio.
        return

    if servidor_activo():
        return

    ruta_server = os.path.join(os.path.dirname(sys.executable), "server", "server.exe")

    if os.path.exists(ruta_server):
        server = subprocess.Popen(
            [ruta_server],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        server = subprocess.Popen(["python", "server.py"])


def esperar_servidor(intentos=15):
    for _ in range(intentos):
        if servidor_activo():
            return True
        time.sleep(1)
    return False


def mostrar_error_conexion():
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "ECUAMINERALES",
        f"No se pudo conectar al servidor en {URL}.\n\n"
        "Verifica que:\n"
        "1. La PC servidor esté encendida y con 'server.exe' corriendo.\n"
        "2. La IP configurada sea correcta.\n"
        "3. Ambas PCs estén en la misma red."
    )
    root.destroy()


def main():
    iniciar_servidor_si_corresponde()

    if not esperar_servidor():
        mostrar_error_conexion()
        sys.exit(1)

    webview.create_window(
        "ECUAMINERALES",
        URL,
        width=1400,
        height=900,
        min_size=(1200, 700)
    )
    webview.start()

    if server:
        server.kill()


if __name__ == "__main__":
    main()