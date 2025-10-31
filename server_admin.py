import socket
import threading
import json
import tkinter as tk
from playsound import playsound
import time

# ===========================
# CONFIGURAÇÕES
# ===========================
HOST = '0.0.0.0'
PORT = 5000

HOUSE_MAP = {
    "Sala": (20, 20, 120, 100),
    "Cozinha": (160, 20, 120, 100),
    "Quarto": (300, 20, 120, 100),
    "Banheiro": (20, 140, 120, 100),
    "Escritório": (160, 140, 120, 100),
    "Porão": (300, 140, 120, 100)
}

state = {
    "lights": {room: False for room in HOUSE_MAP},
    "entities": {room: 0 for room in HOUSE_MAP},
    "visual_glitch": False,       # Glitch visual ativo no operador
    "audio_interference": False,  # Interferência auditiva
    "map": HOUSE_MAP
}

clients = []

# ===========================
# REDE
# ===========================
def handle_client(conn, addr):
    print(f"[+] Operador conectado: {addr}")
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            msg = json.loads(data)
            if msg["type"] == "update_lights":
                state["lights"] = msg["lights"]
                update_interface_buttons()
                broadcast()
    except:
        print(f"[-] Operador desconectado: {addr}")
    finally:
        conn.close()

def broadcast():
    msg = json.dumps(state).encode()
    for c in clients:
        try:
            c.sendall(msg)
        except:
            pass

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Aguardando conexão em {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        broadcast()

threading.Thread(target=start_server, daemon=True).start()

# ===========================
# INTERFACE ADMIN
# ===========================
root = tk.Tk()
root.title("🕯️ Painel do Mestre")

frame_controls = tk.Frame(root)
frame_controls.pack(side=tk.LEFT, padx=10, pady=10)

frame_preview = tk.Frame(root)
frame_preview.pack(side=tk.RIGHT, padx=10, pady=10)

# ---- Luzes ----
tk.Label(frame_controls, text="💡 Controle de Luzes").pack()
buttons_lights = {}
def toggle_light(room):
    state["lights"][room] = not state["lights"][room]
    update_interface_buttons()
    broadcast()

for room in state["lights"]:
    btn = tk.Button(frame_controls, text=f"{room}: OFF", width=18, command=lambda r=room: toggle_light(r))
    btn.pack(pady=2)
    buttons_lights[room] = btn

def update_interface_buttons():
    for room, status in state["lights"].items():
        buttons_lights[room].config(text=f"{room}: {'ON' if status else 'OFF'}")

# ---- Entidades ----
tk.Label(frame_controls, text="\n👁️ Entidades por Cômodo").pack()
entity_labels = {}
def add_entity(room):
    state["entities"][room] += 1
    broadcast()
    update_entity_labels()
def remove_entity(room):
    if state["entities"][room] > 0:
        state["entities"][room] -= 1
    broadcast()
    update_entity_labels()

for room in state["entities"]:
    frame = tk.Frame(frame_controls)
    frame.pack(pady=2)
    tk.Label(frame, text=room).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="+", width=3, command=lambda r=room: add_entity(r)).pack(side=tk.LEFT)
    tk.Button(frame, text="-", width=3, command=lambda r=room: remove_entity(r)).pack(side=tk.LEFT)
    lbl = tk.Label(frame, text="0 entidades")
    lbl.pack(side=tk.LEFT, padx=5)
    entity_labels[room] = lbl

def update_entity_labels():
    for room, count in state["entities"].items():
        entity_labels[room].config(text=f"{count} entidades")

# ---- Efeitos ----
tk.Label(frame_controls, text="\n🔮 Efeitos de Terror").pack()

# ---- Glitch Visual ----
def toggle_visual_glitch():
    state["visual_glitch"] = not state["visual_glitch"]
    broadcast()
btn_glitch = tk.Button(frame_controls, text="⚡ Ligar Glitch Visual", command=toggle_visual_glitch)
btn_glitch.pack(pady=3)

# ---- Interferência Auditiva ----
def toggle_audio_interference():
    state["audio_interference"] = not state["audio_interference"]
    broadcast()
btn_interf = tk.Button(frame_controls, text="📻 Ligar Interferência", command=toggle_audio_interference)
btn_interf.pack(pady=3)

# ---- Mini Mapa do Operador ----
tk.Label(frame_preview, text="📺 Visualização do Operador").pack()
canvas_preview = tk.Canvas(frame_preview, width=460, height=280, bg="black")
canvas_preview.pack(pady=5)

def draw_preview():
    canvas_preview.delete("all")
    for room, coords in state["map"].items():
        x, y, w, h = coords
        light_on = state["lights"].get(room, False)
        entity_count = state["entities"].get(room, 0)
        canvas_preview.create_rectangle(x, y, x+w, y+h, outline="white")
        canvas_preview.create_text(x+w/2, y+h+10, text=room, fill="white")
        light_color = "yellow" if light_on else "gray"
        canvas_preview.create_oval(x+w/2-8, y+h/2-8, x+w/2+8, y+h/2+8, fill=light_color)
        # Entidades lado a lado
        cols = min(5, entity_count)
        for i in range(entity_count):
            col = i % cols
            row = i // cols
            ex = x + 10 + col*(w-20)/cols
            ey = y + 20 + row*10
            canvas_preview.create_oval(ex, ey, ex+8, ey+8, fill="red")
    # Indicativo de glitch visual ativo no operador
    if state["visual_glitch"]:
        canvas_preview.create_text(230, 10, text="GLITCH ATIVO NO OPERADOR", fill="red", font=("Arial", 12, "bold"))

def refresh_preview():
    draw_preview()
    root.after(500, refresh_preview)

refresh_preview()
root.mainloop()
