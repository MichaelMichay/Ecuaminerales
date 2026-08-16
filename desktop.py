import threading
import subprocess
import time
import json
import requests
import webview
import os

CONFIG = "launcher_config.json"

server = None


def cargar_config():

    with open(CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


config = cargar_config()

IP = config["ip"]
PUERTO = config["puerto"]

URL = f"http://{IP}:{PUERTO}"


def servidor_activo():

    try:

        requests.get(URL, timeout=2)

        return True

    except:

        return False


def iniciar_servidor():

    global server

    if servidor_activo():

        return

    if os.path.exists("server.exe"):

        server = subprocess.Popen(
            ["server.exe"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    else:

        server = subprocess.Popen(
            ["python", "server.py"]
        )


def esperar():

    while True:

        try:

            requests.get(URL)

            break

        except:

            time.sleep(1)


threading.Thread(
    target=iniciar_servidor,
    daemon=True
).start()


esperar()


webview.create_window(

    "ECUAMINERALES",

    URL,

    width=1400,

    height=900,

    min_size=(1200,700)

)

webview.start()


if server:

    server.kill()