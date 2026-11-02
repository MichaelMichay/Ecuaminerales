import tkinter as tk
from tkinter import messagebox
import json
import os
import sys
import socket
import subprocess
import requests
import qrcode
from PIL import Image, ImageTk

CONFIG = "launcher_config.json"

# URLs del sistema tras aplicar el modo público
RUTA_PUBLICA   = "/"          # página pública (raíz)
RUTA_SISTEMA   = "/sistema/"  # login / panel administrativo


# ─────────────────────────────────────────────
# Detectar IP local de la red
# ─────────────────────────────────────────────
def obtener_ip_local():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


# ─────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────
def cargar_config():
    if os.path.exists(CONFIG):
        try:
            with open(CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass
    return {"ip": obtener_ip_local(), "puerto": 8000}


def validar_campos():
    ip = txt_ip.get().strip()
    puerto_str = txt_puerto.get().strip()

    if not ip:
        messagebox.showwarning("Validación", "Ingrese la dirección IP del servidor.")
        txt_ip.focus()
        return None, None

    try:
        puerto = int(puerto_str)
        if not (1 <= puerto <= 65535):
            raise ValueError
    except ValueError:
        messagebox.showwarning("Validación", "El puerto debe ser un número entre 1 y 65535.")
        txt_puerto.focus()
        return None, None

    return ip, puerto


def guardar():
    ip, puerto = validar_campos()
    if ip is None:
        return False

    datos = {
        "ip": ip,
        "puerto": puerto,
        "recordar": True,
        "nombre_empresa": "ECUAMINERALES S.A.",
        "version": "1.0.0"
    }

    try:
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4)
        messagebox.showinfo("Correcto", "Configuración guardada correctamente.")
        actualizar_qr()
        return True
    except OSError as e:
        messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{e}")
        return False


# ─────────────────────────────────────────────
# Probar conexión — verifica /sistema/ (login)
# ─────────────────────────────────────────────
def probar():
    ip, puerto = validar_campos()
    if ip is None:
        return

    url = f"http://{ip}:{puerto}{RUTA_SISTEMA}"
    lbl_estado.config(text="Probando conexión...", fg="#555555")
    ventana.update_idletasks()

    try:
        respuesta = requests.get(url, timeout=3)
        lbl_estado.config(
            text=f"✔ Servidor activo  (HTTP {respuesta.status_code})",
            fg="green"
        )
    except requests.exceptions.ConnectionError:
        lbl_estado.config(text="✘ No se pudo conectar al servidor", fg="red")
    except requests.exceptions.Timeout:
        lbl_estado.config(text="✘ Tiempo de espera agotado", fg="red")
    except requests.exceptions.RequestException as e:
        lbl_estado.config(text=f"✘ Error: {e}", fg="red")


# ─────────────────────────────────────────────
# Abrir sistema de escritorio
# ─────────────────────────────────────────────
def abrir():
    if not guardar():
        return

    ruta_desktop = os.path.join(
        os.path.dirname(sys.executable),
        "ECUMINERALES_DESKTOP.exe"
    )

    if not os.path.exists(ruta_desktop):
        messagebox.showerror(
            "Error",
            f"No se encontró el ejecutable:\n{ruta_desktop}"
        )
        return

    try:
        subprocess.Popen(
            [ruta_desktop],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        ventana.destroy()
    except OSError as e:
        messagebox.showerror("Error", f"No se pudo abrir la aplicación:\n{e}")


# ─────────────────────────────────────────────
# QR — apunta a la página PÚBLICA (raíz "/")
# para que cualquier equipo de la red entre
# directamente al portal de Ecuaminerales.
# ─────────────────────────────────────────────
def generar_qr(url: str, size: int = 170) -> ImageTk.PhotoImage:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=5,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size), Image.LANCZOS)
    return ImageTk.PhotoImage(img)


def actualizar_qr():
    ip     = txt_ip.get().strip()     or "127.0.0.1"
    puerto = txt_puerto.get().strip() or "8000"

    # El QR lleva a la página pública para los demás equipos
    url_publica  = f"http://{ip}:{puerto}{RUTA_PUBLICA}"
    url_sistema  = f"http://{ip}:{puerto}{RUTA_SISTEMA}"

    try:
        foto = generar_qr(url_publica)
        lbl_qr.config(image=foto, text="")
        lbl_qr.image = foto
        lbl_url_qr.config(text=f"Pública:  {url_publica}\nSistema:  {url_sistema}")
    except Exception as e:
        lbl_qr.config(image="", text=f"Error al generar QR:\n{e}")


# =====================================================
# VENTANA PRINCIPAL
# =====================================================

config = cargar_config()

ventana = tk.Tk()
ventana.title("ECUAMINERALES — Configuración del Servidor")
ventana.geometry("660x430")
ventana.resizable(False, False)

# Layout: izquierda (controles) | derecha (QR)
frame_izq = tk.Frame(ventana, padx=20, pady=15)
frame_izq.pack(side=tk.LEFT, fill=tk.BOTH)

frame_der = tk.Frame(ventana, padx=10, pady=15, bg="#F4F4F4", relief=tk.GROOVE, bd=1)
frame_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# ── Columna izquierda ─────────────────────────────

tk.Label(
    frame_izq,
    text="ECUAMINERALES",
    font=("Arial", 18, "bold"),
    fg="#1F4E79"
).pack(pady=(0, 2))

tk.Label(
    frame_izq,
    text="Configuración del Servidor",
    font=("Arial", 11)
).pack()

# Campos
frame_campos = tk.Frame(frame_izq)
frame_campos.pack(pady=12)

tk.Label(frame_campos, text="IP Servidor", anchor="e", width=12).grid(
    row=0, column=0, padx=8, pady=8, sticky="e"
)
txt_ip = tk.Entry(frame_campos, width=22)
txt_ip.grid(row=0, column=1)
txt_ip.insert(0, config.get("ip", obtener_ip_local()))

def detectar_ip():
    ip = obtener_ip_local()
    txt_ip.delete(0, tk.END)
    txt_ip.insert(0, ip)
    actualizar_qr()

tk.Button(
    frame_campos, text="🔍", command=detectar_ip,
    width=2, relief=tk.FLAT, bg="#E0E0E0", cursor="hand2"
).grid(row=0, column=2, padx=4)

tk.Label(frame_campos, text="Puerto", anchor="e", width=12).grid(
    row=1, column=0, padx=8, pady=6, sticky="e"
)
txt_puerto = tk.Entry(frame_campos, width=10)
txt_puerto.grid(row=1, column=1, sticky="w")
txt_puerto.insert(0, config.get("puerto", 8000))

# Leyenda de rutas
frame_rutas = tk.Frame(frame_izq, bg="#EEF4FF", bd=1, relief=tk.GROOVE)
frame_rutas.pack(fill=tk.X, pady=(0, 8))
tk.Label(
    frame_rutas,
    text="  /              → Página pública\n  /sistema/  → Login del sistema",
    font=("Courier", 9),
    bg="#EEF4FF",
    fg="#333",
    justify=tk.LEFT,
    anchor="w"
).pack(padx=8, pady=6, anchor="w")

# QR se regenera al escribir
txt_ip.bind("<KeyRelease>", lambda e: actualizar_qr())
txt_puerto.bind("<KeyRelease>", lambda e: actualizar_qr())

# Estado de conexión
lbl_estado = tk.Label(frame_izq, text="", font=("Arial", 9))
lbl_estado.pack(pady=(0, 4))

# Botones
tk.Button(
    frame_izq, text="Probar conexión",
    width=24, bg="#17A2B8", fg="white",
    command=probar, cursor="hand2"
).pack(pady=3)

tk.Button(
    frame_izq, text="Guardar configuración",
    width=24, bg="#28A745", fg="white",
    command=guardar, cursor="hand2"
).pack(pady=3)

tk.Button(
    frame_izq, text="Abrir ECUAMINERALES",
    width=24, bg="#0D6EFD", fg="white",
    command=abrir, cursor="hand2"
).pack(pady=10)

# ── Columna derecha (QR) ──────────────────────────

tk.Label(
    frame_der,
    text="Conectar otro equipo",
    font=("Arial", 11, "bold"),
    bg="#F4F4F4"
).pack(pady=(5, 2))

tk.Label(
    frame_der,
    text="Escanea para abrir la\npágina pública",
    font=("Arial", 8),
    fg="#555555",
    bg="#F4F4F4"
).pack()

lbl_qr = tk.Label(frame_der, bg="#F4F4F4")
lbl_qr.pack(pady=8)

lbl_url_qr = tk.Label(
    frame_der,
    text="",
    font=("Courier", 7),
    fg="#333333",
    bg="#F4F4F4",
    justify=tk.LEFT,
    wraplength=190
)
lbl_url_qr.pack()

# QR inicial
actualizar_qr()

ventana.mainloop()