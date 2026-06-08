"""
RemoteDesk - Servidor WebSocket
Controla mouse, teclado y transmite pantalla desde el PC.
Requiere: pip install websockets pynput mss pillow
"""

import asyncio
import websockets
import json
import base64
import io
import time
import logging
from pathlib import Path

# Control de mouse y teclado
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

# Captura de pantalla
import mss
from PIL import Image

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("RemoteDesk")

mouse    = MouseController()
keyboard = KeyboardController()

# ── Configuración ────────────────────────────────────────────────
HOST         = "0.0.0.0"   # escucha en todas las interfaces
PORT         = 8765
STREAM_FPS   = 10          # fotogramas por segundo del stream
STREAM_QUALITY = 40        # calidad JPEG (1-95); menor = más rápido
STREAM_SCALE   = 0.5       # factor de escala de la captura (0.0-1.0)

# ── Teclas especiales mapeadas ───────────────────────────────────
SPECIAL_KEYS = {
    "Enter": Key.enter, "Backspace": Key.backspace, "Tab": Key.tab,
    "Escape": Key.esc, "Space": Key.space,
    "ArrowUp": Key.up, "ArrowDown": Key.down,
    "ArrowLeft": Key.left, "ArrowRight": Key.right,
    "Delete": Key.delete, "Home": Key.home, "End": Key.end,
    "PageUp": Key.page_up, "PageDown": Key.page_down,
    "F1": Key.f1, "F2": Key.f2, "F3": Key.f3, "F4": Key.f4,
    "F5": Key.f5, "F6": Key.f6, "F7": Key.f7, "F8": Key.f8,
    "Control": Key.ctrl, "Alt": Key.alt, "Shift": Key.shift,
    "Meta": Key.cmd, "CapsLock": Key.caps_lock,
}

# ── Captura de pantalla ──────────────────────────────────────────
def capture_screen(scale: float = STREAM_SCALE, quality: int = STREAM_QUALITY) -> str:
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # monitor principal
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    if scale < 1.0:
        w = int(img.width * scale)
        h = int(img.height * scale)
        img = img.resize((w, h), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

# ── Procesamiento de comandos ────────────────────────────────────
def handle_command(data: dict) -> dict:
    cmd  = data.get("cmd")
    resp = {"ok": True}

    try:
        # ── Mouse ────────────────────────────────────────────────
        if cmd == "mouse_move":
            mouse.position = (int(data["x"]), int(data["y"]))

        elif cmd == "mouse_move_rel":
            dx, dy = int(data["dx"]), int(data["dy"])
            x, y = mouse.position
            mouse.position = (x + dx, y + dy)

        elif cmd == "mouse_click":
            btn = Button.right if data.get("button") == "right" else Button.left
            mouse.click(btn, int(data.get("count", 1)))

        elif cmd == "mouse_down":
            btn = Button.right if data.get("button") == "right" else Button.left
            mouse.press(btn)

        elif cmd == "mouse_up":
            btn = Button.right if data.get("button") == "right" else Button.left
            mouse.release(btn)

        elif cmd == "mouse_scroll":
            mouse.scroll(int(data.get("dx", 0)), int(data.get("dy", 0)))

        # ── Teclado ──────────────────────────────────────────────
        elif cmd == "key_press":
            key_str = data.get("key", "")
            key = SPECIAL_KEYS.get(key_str, key_str if len(key_str) == 1 else None)
            if key:
                keyboard.press(key)
                keyboard.release(key)

        elif cmd == "key_down":
            key_str = data.get("key", "")
            key = SPECIAL_KEYS.get(key_str, key_str if len(key_str) == 1 else None)
            if key:
                keyboard.press(key)

        elif cmd == "key_up":
            key_str = data.get("key", "")
            key = SPECIAL_KEYS.get(key_str, key_str if len(key_str) == 1 else None)
            if key:
                keyboard.release(key)

        elif cmd == "type_text":
            keyboard.type(data.get("text", ""))

        # ── Info del servidor ────────────────────────────────────
        elif cmd == "ping":
            resp["pong"] = True

        elif cmd == "get_info":
            import platform, socket
            resp["os"]   = platform.system()
            resp["node"] = platform.node()
            resp["ip"]   = socket.gethostbyname(socket.gethostname())
            x, y = mouse.position
            resp["mouse"] = {"x": x, "y": y}

        else:
            resp = {"ok": False, "error": f"Comando desconocido: {cmd}"}

    except Exception as e:
        resp = {"ok": False, "error": str(e)}
        log.error(f"Error ejecutando '{cmd}': {e}")

    return resp

# ── Manejo de conexiones WebSocket ───────────────────────────────
connected_clients: set = set()

async def handler(websocket):
    client_ip = websocket.remote_address[0]
    log.info(f"Cliente conectado: {client_ip}")
    connected_clients.add(websocket)

    stream_task = None

    try:
        async for raw in websocket:
            data = json.loads(raw)

            # Comando de stream de pantalla
            if data.get("cmd") == "start_stream":
                fps     = data.get("fps", STREAM_FPS)
                quality = data.get("quality", STREAM_QUALITY)
                scale   = data.get("scale", STREAM_SCALE)

                if stream_task:
                    stream_task.cancel()

                async def stream_loop(ws=websocket, fps=fps, quality=quality, scale=scale):
                    interval = 1.0 / fps
                    while True:
                        try:
                            frame = capture_screen(scale, quality)
                            await ws.send(json.dumps({"type": "frame", "data": frame}))
                            await asyncio.sleep(interval)
                        except Exception:
                            break

                stream_task = asyncio.create_task(stream_loop())
                await websocket.send(json.dumps({"ok": True, "streaming": True}))
                continue

            elif data.get("cmd") == "stop_stream":
                if stream_task:
                    stream_task.cancel()
                    stream_task = None
                await websocket.send(json.dumps({"ok": True, "streaming": False}))
                continue

            elif data.get("cmd") == "snapshot":
                quality = data.get("quality", STREAM_QUALITY)
                scale   = data.get("scale", STREAM_SCALE)
                frame   = capture_screen(scale, quality)
                await websocket.send(json.dumps({"type": "frame", "data": frame}))
                continue

            # Comandos normales
            result = handle_command(data)
            await websocket.send(json.dumps(result))

    except websockets.exceptions.ConnectionClosedOK:
        log.info(f"Cliente desconectado: {client_ip}")
    except Exception as e:
        log.error(f"Error con {client_ip}: {e}")
    finally:
        connected_clients.discard(websocket)
        if stream_task:
            stream_task.cancel()

# ── Punto de entrada ─────────────────────────────────────────────
async def main():
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    log.info("=" * 50)
    log.info("  RemoteDesk Server")
    log.info("=" * 50)
    log.info(f"  IP local  : {local_ip}")
    log.info(f"  Puerto    : {PORT}")
    log.info(f"  URL celular: ws://{local_ip}:{PORT}")
    log.info("=" * 50)
    log.info("  Presiona Ctrl+C para detener")

    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
