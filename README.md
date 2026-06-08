# 🖥️ RemoteDesk

> Controla tu PC desde el celular — mouse, teclado y stream de pantalla en tiempo real.  
> Sin apps, sin instalaciones en el móvil. Solo abre el navegador.

---

## ¿Qué hace?

| Función | Descripción |
|---|---|
| 🖱 **Touchpad** | Desliza para mover el mouse · Toca dos veces para doble clic |
| 👆 **Clics** | Botones para clic izquierdo y derecho |
| 🔃 **Scroll** | Dos dedos en el touchpad o botones laterales |
| ⌨️ **Teclado** | Escribe texto, teclas especiales, flechas, F1-F8 |
| ⌨️ **Atajos** | Ctrl+C/V/Z, Alt+Tab, Win+D y más con un toque |
| 🖥️ **Stream** | Visualiza tu pantalla en tiempo real (~10 fps) |
| 📸 **Snapshot** | Captura instantánea de alta calidad |

---

## Requisitos

**En el PC:**
- Python 3.8+
- Windows, macOS o Linux

**En el celular:**
- Cualquier navegador moderno (Chrome, Firefox, Safari)
- En la misma red WiFi **o** con el PC conectado al hotspot del celular

---

## Instalación

### 1. Clona el repositorio

```bash
git clone https://github.com/TU_USUARIO/remotedesk.git
cd remotedesk
```

### 2. Instala las dependencias del servidor

```bash
cd server
pip install -r requirements.txt
```

### 3. Inicia el servidor en el PC

```bash
python server.py
```

Verás algo así:

```
[10:32:14] ==================================================
[10:32:14]   RemoteDesk Server
[10:32:14] ==================================================
[10:32:14]   IP local  : 192.168.1.15
[10:32:14]   Puerto    : 8765
[10:32:14]   URL celular: ws://192.168.1.15:8765
[10:32:14] ==================================================
```

### 4. Abre el cliente en el celular

**Opción A — Archivo local:**  
Abre `client/index.html` directamente desde el celular (descárgalo o accede por red).

**Opción B — GitHub Pages:**  
Activa GitHub Pages en tu repo apuntando a la carpeta `/client` y visita la URL desde el móvil.

**Opción C — Servidor local rápido:**
```bash
# En la carpeta client/
python -m http.server 8080
# Luego visita: http://192.168.1.15:8080
```

### 5. Conéctate

En la pantalla de inicio del cliente, ingresa la IP y el puerto mostrados en la terminal del PC → **Conectar**.

---

## Uso sin WiFi (solo hotspot)

1. Activa el **hotspot** en tu celular
2. Conecta el PC a esa red WiFi
3. La IP del servidor cambiará — vuelve a ver la terminal del PC para obtenerla
4. Conéctate desde el navegador del celular con esa nueva IP

---

## Estructura del proyecto

```
remotedesk/
├── server/
│   ├── server.py          # Servidor WebSocket + control de mouse/teclado
│   └── requirements.txt   # Dependencias Python
├── client/
│   └── index.html         # Cliente web (todo en un archivo)
└── README.md
```

---

## Configuración avanzada

Edita las constantes al inicio de `server/server.py`:

```python
PORT           = 8765   # Puerto del servidor
STREAM_FPS     = 10     # Fotogramas por segundo del stream
STREAM_QUALITY = 40     # Calidad JPEG (1-95)
STREAM_SCALE   = 0.5    # Escala de captura (0.3 = muy rápido, 1.0 = full HD)
```

---

## Seguridad

> ⚠️ RemoteDesk está diseñado para uso en **redes locales de confianza**.  
> No expongas el puerto 8765 a internet sin autenticación adicional.

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Servidor | Python · `websockets` · `pynput` · `mss` · `Pillow` |
| Cliente | HTML5 · CSS3 · JavaScript vanilla |
| Protocolo | WebSocket (JSON + base64 para frames) |

---

## Licencia

MIT — úsalo, modifícalo, compártelo.
