import tkinter as tk
from tkinter import messagebox
import json
import os
import subprocess
import requests

CONFIG = "launcher_config.json"


# -----------------------------
# Leer configuración
# -----------------------------
def cargar_config():

    if os.path.exists(CONFIG):

        with open(CONFIG, "r", encoding="utf-8") as archivo:
            return json.load(archivo)

    return {
        "ip": "127.0.0.1",
        "puerto": 8000
    }


# -----------------------------
# Guardar configuración
# -----------------------------
def guardar():

    datos = {
        "ip": txt_ip.get(),
        "puerto": int(txt_puerto.get()),
        "recordar": True,
        "nombre_empresa": "ECUAMINERALES S.A.",
        "version": "1.0.0"
    }

    with open(CONFIG, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4)

    messagebox.showinfo(
        "Correcto",
        "Configuración guardada correctamente."
    )


# -----------------------------
# Probar conexión
# -----------------------------
def probar():

    ip = txt_ip.get()
    puerto = txt_puerto.get()

    url = f"http://{ip}:{puerto}"

    try:

        requests.get(url, timeout=3)

        lbl_estado.config(
            text="Servidor encontrado",
            fg="green"
        )

    except:

        lbl_estado.config(
            text="No se pudo conectar",
            fg="red"
        )


# -----------------------------
# Abrir sistema
# -----------------------------
def abrir():

    guardar()

    ventana.destroy()

    subprocess.Popen(["python", "desktop.py"])


# -----------------------------
# Ventana
# -----------------------------

config = cargar_config()

ventana = tk.Tk()

ventana.title("ECUAMINERALES")

ventana.geometry("450x350")

ventana.resizable(False, False)

# -----------------------------

titulo = tk.Label(

    ventana,

    text="ECUAMINERALES",

    font=("Arial", 20, "bold"),

    fg="#1F4E79"

)

titulo.pack(pady=10)

sub = tk.Label(

    ventana,

    text="Configuración del Servidor",

    font=("Arial", 12)

)

sub.pack()

# -----------------------------

frame = tk.Frame(ventana)

frame.pack(pady=15)

tk.Label(

    frame,

    text="IP Servidor"

).grid(row=0, column=0, padx=10, pady=10)

txt_ip = tk.Entry(frame, width=25)

txt_ip.grid(row=0, column=1)

txt_ip.insert(0, config["ip"])

# -----------------------------

tk.Label(

    frame,

    text="Puerto"

).grid(row=1, column=0)

txt_puerto = tk.Entry(frame, width=10)

txt_puerto.grid(row=1, column=1)

txt_puerto.insert(0, config["puerto"])

# -----------------------------

lbl_estado = tk.Label(

    ventana,

    text="",

    font=("Arial",10)

)

lbl_estado.pack()

# -----------------------------

tk.Button(

    ventana,

    text="Probar conexión",

    width=25,

    bg="#17A2B8",

    fg="white",

    command=probar

).pack(pady=5)

# -----------------------------

tk.Button(

    ventana,

    text="Guardar configuración",

    width=25,

    bg="#28A745",

    fg="white",

    command=guardar

).pack(pady=5)

# -----------------------------

tk.Button(

    ventana,

    text="Abrir ECUAMINERALES",

    width=25,

    bg="#0D6EFD",

    fg="white",

    command=abrir

).pack(pady=15)

ventana.mainloop()