# python
import socket
import threading
import json
import tkinter as tk
from tkinter import messagebox
import pygame
import time
import random

SERVER_IP = '127.0.0.1'
PORT = 5000

pygame.mixer.init()
state = {
    "lights": {},
    "entities": {},
    "visual_glitch": False,
    "audio_interference": False,
    "sound_whisper": False,
    "map": {}
}

sock = None  # will be created after login

root = tk.Tk()
root.title("💡 Painel do Operador")
root.withdraw()  # hide main window until connected

canvas = tk.Canvas(root, width=460, height=280, bg="black")
canvas.pack(pady=5)

text_log = tk.Text(root, height=6, width=60)
text_log.pack(pady=5)

buttons = {}
glitch_played = False  # indica se a animação do glitch já ocorreu


def log(msg):
    text_log.insert(tk.END, msg + "\n")
    text_log.see(tk.END)


def send_update():
    global sock
    if not sock:
        log("[Erro] Não conectado ao servidor")
        return
    try:
        msg = {"type": "update_lights", "lights": state["lights"]}
        sock.sendall(json.dumps(msg).encode())
    except Exception as e:
        log(f"[Erro] Falha ao enviar: {e}")


def receive_updates():
    global sock
    while True:
        try:
            data = sock.recv(4096).decode()
            if not data:
                break
            new_state = json.loads(data)
            update_state(new_state)
        except:
            break
    log("[Conexão encerrada]")


def update_state(new_state):
    global state, glitch_played
    prev_glitch = state["visual_glitch"]
    state.update(new_state)

    # reset da animação apenas se glitch foi desligado
    if prev_glitch and not state["visual_glitch"]:
        glitch_played = False

    update_ui()


def toggle_light(room):
    state["lights"][room] = not state["lights"][room]
    send_update()


def draw_map():
    canvas.delete("all")
    if state.get("visual_glitch"):
        global glitch_played
        if not glitch_played:
            # animação de bug apenas uma vez
            for _ in range(6):
                canvas.delete("all")
                canvas.create_rectangle(0, 0, 460, 280, fill=random.choice(["white", "gray", "black"]))
                root.update()
                time.sleep(0.05)
            glitch_played = True
        # tela permanece preta até glitch ser desligado
        canvas.create_rectangle(0, 0, 460, 280, fill="black")
        return

    # Desenhar mapa normalmente
    for room, coords in state["map"].items():
        x, y, w, h = coords
        light_on = state["lights"].get(room, False)
        entity_count = state["entities"].get(room, 0)
        canvas.create_rectangle(x, y, x + w, y + h, outline="white")
        canvas.create_text(x + w / 2, y + h + 10, text=room, fill="white")
        light_color = "yellow" if light_on else "gray"
        canvas.create_oval(x + w / 2 - 8, y + h / 2 - 8, x + w / 2 + 8, y + h / 2 + 8, fill=light_color)
        # Entidades lado a lado
        cols = min(5, entity_count)
        for i in range(entity_count):
            col = i % cols
            row = i // cols
            ex = x + 10 + col * (w - 20) / cols
            ey = y + 20 + row * 10
            canvas.create_oval(ex, ey, ex + 8, ey + 8, fill="red")


def update_ui():
    draw_map()

    # Interferência auditiva
    if state.get("audio_interference"):
        if not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.load("sons/static.mp3")
                pygame.mixer.music.play(-1)
                log("[Interferência auditiva ativa]")
            except:
                log("[Erro] Não foi possível tocar a interferência")
    else:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            log("[Interferência auditiva desligada]")

    # Botões de luzes
    for room in state["map"]:
        if room not in buttons:
            btn = tk.Button(root, text=f"Alternar {room}", command=lambda r=room: toggle_light(r))
            btn.pack(pady=2)
            buttons[room] = btn


# --- Login dialog ---
def open_login():
    login = tk.Toplevel()
    login.title("Login - Conectar ao servidor")
    login.geometry("300x140")
    login.resizable(False, False)

    tk.Label(login, text="Server IP:").pack(pady=(10, 0))
    ip_entry = tk.Entry(login)
    ip_entry.insert(0, SERVER_IP)
    ip_entry.pack()

    tk.Label(login, text="Port:").pack(pady=(8, 0))
    port_entry = tk.Entry(login)
    port_entry.insert(0, str(PORT))
    port_entry.pack()

    def attempt_connect():
        ip = ip_entry.get().strip()
        try:
            port = int(port_entry.get().strip())
        except:
            messagebox.showerror("Erro", "Porta inválida")
            return
        connect_to_server(ip, port, login)

    tk.Button(login, text="Conectar", command=attempt_connect).pack(pady=10)
    login.protocol("WM_DELETE_WINDOW", root.quit)


def connect_to_server(ip, port, login_window):
    global sock
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        sock = s
        log(f"[Conectado com sucesso a rede!]")
        # start receiving thread
        threading.Thread(target=receive_updates, daemon=True).start()
        # show main window
        root.deiconify()
        login_window.destroy()
    except Exception as e:
        messagebox.showerror("Erro de conexão", f"Não foi possível conectar: {e}")


# Start login then main loop
open_login()
root.mainloop()
