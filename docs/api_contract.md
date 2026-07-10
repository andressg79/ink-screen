# Contrato de la API de Alertas RPG y Biblioteca de Sprites

Este documento define la biblioteca de sprites pixel art disponibles y el contrato de los endpoints de la API REST para interactuar con el módulo de alertas de pantalla completa.

---

## 🎨 Biblioteca de Pixel Art

Las alertas de pantalla completa muestran un retrato pixel art monocromático (blanco y negro) en el lado izquierdo. El retrato está definido originalmente en una rejilla de **32x32 píxeles** y se escala a **64x64 píxeles** usando interpolación de vecindario más cercano para preservar el estilo retro 8-bits.

Están disponibles los siguientes personajes para el campo `image_id`, los cuales se pueden enviar tanto por su ID numérico (entero) como por su nombre (string):

| ID | Nombre | Descripción |
| :--- | :--- | :--- |
| **1** | `caballero` | Casco de caballero con visor abierto, hablando en plano medio corto. |
| **2** | `brujo` | Mago con capucha larga y ojos oscuros hablando. |
| **3** | `bruja` | Bruja con sombrero puntiagudo y boca abierta hablando. |
| **4** | `nigromante` | Esqueleto con capucha oscura y mandíbula abierta. |
| **5** | `elfo` | Elfo con orejas puntiagudas y cabello liso hablando. |
| **6** | `ogro` | Ogro de mandíbula ancha con colmillo central visible hablando. |
| **7** | `enano` / `enano minero` | Enano con casco de minero y gran barba tupida hablando. |
| **8** | `doncella` | Doncella con cabello largo y tiara en la frente hablando. |
| **9** | `paisano` | Aldeano/paisano con gorra simple y ropa modesta hablando. *(Valor por defecto)* |

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
  "image_id": "elfo",
  "duration": 30,
  "footer": "⌛ [ ESPERANDO ACCION... ]"
}
```

*   `title` (Requerido, string): Título centrado en la parte superior. Largo: **1 a 25 caracteres**.
*   `text` (Requerido, string): Mensaje principal a mostrar. Largo: **1 a 120 caracteres** (con ajuste de línea automático).
*   `image_id` (Requerido, entero o string): ID numérico (1-9) o nombre string del retrato de la biblioteca.
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
      "image_id": 1,
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
*   **Descripción:** Devuelve el estado actual de conexión, la telemetría del sistema, el clima almacenado en caché y los detalles de las alertas activas.

#### Respuesta (`200 OK`)
```json
{
  "status": "online",
  "custom_message": null,
  "custom_message_expires_in": null,
  "alert_active": true,
  "alert_title": "Alerta de Sistema",
  "alert_text": "Se ha detectado una anomalía en el reactor central. ¡Evacuar inmediatamente!",
  "alert_image_id": 1,
  "alert_expires_in": 18.5,
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
  }
}
```
