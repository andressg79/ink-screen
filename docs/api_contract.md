# Contrato de la API de Alertas RPG y Biblioteca de Sprites

Este documento define la biblioteca de sprites pixel art disponibles y el contrato de los endpoints de la API REST para interactuar con el módulo de alertas de pantalla completa.

---

## 🎨 Biblioteca de Pixel Art

Las alertas de pantalla completa muestran un retrato pixel art monocromático (blanco y negro) en el lado izquierdo. El retrato está definido originalmente en una rejilla de **32x32 píxeles** y se escala a **64x64 píxeles** usando interpolación de vecindario más cercano para preservar el estilo retro 8-bits.

Están disponibles los siguientes personajes para el campo `avatar` (corresponden a los archivos `.txt` cargados en la carpeta `assets/`):

| Nombre | Archivo | Descripción |
| :--- | :--- | :--- |
| `caballero` | `assets/caballero.txt` | Casco de caballero con visor abierto, hablando en plano medio corto. |
| `brujo` | `assets/brujo.txt` | Mago con capucha larga y ojos oscuros hablando. |
| `bruja` | `assets/bruja.txt` | Bruja con sombrero puntiagudo y boca abierta hablando. |
| `nigromante` | `assets/nigromante.txt` | Esqueleto con capucha oscura y mandíbula abierta. |
| `elfo` | `assets/elfo.txt` | Elfo con orejas puntiagudas y cabello liso hablando. |
| `ogro` | `assets/ogro.txt` | Ogro de mandíbula ancha con colmillo central visible hablando. |
| `enano` | `assets/enano.txt` | Enano con casco de minero y gran barba tupida hablando. |
| `doncella` | `assets/doncella.txt` | Doncella con cabello largo y tiara en la frente hablando. |
| `paisano` | `assets/paisano.txt` | Aldeano/paisano con gorra simple y ropa modesta hablando. *(Valor por defecto)* |

---

## 🌐 Contrato de la API REST

Todos los endpoints tienen el prefijo `/api`.

### 1. Publicar Alerta RPG
*   **Método:** `POST`
*   **Ruta:** `/api/alert`
*   **Descripción:** Muestra un mensaje a pantalla completa con diseño retro RPG por un tiempo determinado. Si hay otra alerta activa, rechaza la solicitud.

#### Cuerpo de la Solicitud (JSON)
```json
{
  "title": "Alerta de Sistema",
  "text": "Se ha detectado una anomalía en el reactor central. ¡Evacuar inmediatamente!",
  "avatar": "elfo",
  "duration": 30,
  "footer": "⌛ [ ESPERANDO ACCION... ]"
}
```

*   `title` (Requerido, string): Título centrado en la parte superior. Largo: **1 a 25 caracteres**.
*   `text` (Requerido, string): Mensaje principal a mostrar. Largo: **1 a 120 caracteres** (con ajuste de línea automático).
*   `avatar` (Requerido, string): Nombre del avatar RPG a mostrar (nombre del archivo `.txt` en la carpeta `assets/`, sin extensión).
*   `duration` (Requerido, entero): Duración de visualización en segundos. Rango: **5 a 86400 segundos** (24 horas).
*   `footer` (Opcional, string): Texto personalizado para el pie de pantalla invertido. Largo: **máximo 40 caracteres**. Por defecto: `"⌛ [ ESPERANDO... ]"`.

#### Respuestas
*   **`200 OK`**: Alerta aceptada y renderizada con éxito.
    ```json
    {
      "status": "success",
      "message": "Alerta recibida. Actualizando pantalla...",
      "title": "Alerta de Sistema",
      "text": "Se ha detectado una anomalía en el reactor central. ¡Evacuar inmediatamente!",
      "avatar": "caballero",
      "duration": 30,
      "expires_at": 1783300400.0,
      "footer": "⌛ [ ESPERANDO ACCION... ]"
    }
    ```
*   **`409 Conflict`**: Ya hay otra alerta activa mostrándose en el dispositivo.
    ```json
    {
      "detail": "Ya hay una alerta activa en pantalla. Espere a que expire o bórrela manualmente."
    }
    ```
*   **`422 Unprocessable Entity`**: Error de validación en los tipos o límites de los datos provistos.

---

### 2. Limpiar Alerta Activa
*   **Método:** `POST`
*   **Ruta:** `/api/alert/clear`
*   **Descripción:** Quita de forma inmediata cualquier alerta RPG de pantalla completa activa y fuerza el retorno al estado por defecto (o al mensaje de footer anterior si no ha expirado).

#### Respuestas
*   **`200 OK`**:
    ```json
    {
      "status": "success",
      "message": "Alerta RPG borrada. Actualizando pantalla..."
    }
    ```

---

### 3. Consultar Estado del Dispositivo
*   **Método:** `GET`
*   **Ruta:** `/api/status`
*   **Descripción:** Devuelve el estado actual de conexión, la telemetría del sistema, el clima, las métricas del nodo de minería XMRig, el estado del carrusel de pantallas y las alertas activas.

#### Respuesta (`200 OK`)
```json
{
  "status": "online",
  "custom_message": null,
  "custom_message_expires_in": null,
  "alert_active": false,
  "alert_title": null,
  "alert_text": null,
  "alert_avatar": null,
  "alert_expires_in": null,
  "refresh_count": 42,
  "last_full_refresh": "2026-07-09 01:40:02",
  "last_partial_refresh": "2026-07-09 01:45:00",
  "system": {
    "cpu": 12.3,
    "temp": 41.5,
    "ram": 48.2,
    "disk": 22.8,
    "ip": "192.168.1.253",
    "uptime": "2d 5h 20m"
  },
  "weather": {
    "temp": "22.5",
    "condition": "Soleado",
    "icon": "☀️",
    "humidity": "45%",
    "wind": "12 km/h"
  },
  "miner": {
    "status": "MINANDO",
    "hashrate_10s": 124.5,
    "hashrate_60s": 121.0,
    "hashrate_15m": 118.2,
    "hashrate_max": 148.2,
    "shares_good": 42,
    "shares_total": 42,
    "shares_rejected": 0,
    "diff": 1280169,
    "diff_formatted": "1.28M",
    "pool": "gulf.moneroocean.stream:20128",
    "uptime": "4h 12m",
    "algo": "rx/0",
    "threads": 8,
    "hugepages": "100%",
    "paused": false,
    "raw_error": null
  },
  "screen": {
    "current_name": "system",
    "current_title": "Sistema y Clima",
    "current_index": 1,
    "total_screens": 2,
    "next_name": "miner",
    "next_title": "Nodo Minero XMRig",
    "time_remaining_sec": 45,
    "rotation_enabled": true,
    "is_forced": false
  }
}
```

---

### 4. Controlar o Fijar Pantalla del Carrusel
*   **Método:** `POST`
*   **Ruta:** `/api/screen/{screen_name}`
*   **Descripción:** Fija una pantalla específica (ej: `system`, `miner`) o reanuda la alternancia automática (`auto` o `none`).

#### Parámetros de Ruta
*   `screen_name` (string): Nombre de la pantalla a fijar (`"system"`, `"miner"`) o `"auto"` / `"none"` para volver a la rotación automática cíclica.

#### Respuestas
*   **`200 OK`**: Pantalla cambiada o rotación reanudada exitosamente.
    ```json
    {
      "status": "success",
      "message": "Pantalla fijada a 'miner'. Actualizando pantalla..."
    }
    ```
*   **`400 Bad Request`**: Si el nombre de pantalla provisto no existe.

