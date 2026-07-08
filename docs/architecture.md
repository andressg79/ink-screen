# Arquitectura del Software

Este documento detalla la estructura del software para el servicio de despliegue de información en la pantalla E-Ink ZJYE290S08W0G01 usando una Orange Pi RV2.

## Módulos del Sistema

El software está dividido en varios módulos con responsabilidades claras:

```
src/
├── main.py            # Punto de entrada, coordina el servidor FastAPI y el daemon
├── api.py             # Definición de rutas y endpoints de la API
├── system_info.py     # Captura de métricas del sistema (CPU, RAM, Disco, Temp)
├── weather.py         # Cliente HTTP para consultar el clima actual (Open-Meteo)
├── renderer.py        # Generación de la imagen usando Pillow (UI Layout)
└── driver/
    ├── __init__.py
    ├── epd2in9_v2.py  # Driver de bajo nivel para e-paper 2.9" V2 (SSD1680)
    └── epdconfig.py   # Configuración de hardware (SPI3 y GPIO sysfs en RISC-V)
```

---

## 1. Módulos Core

### `src/system_info.py`
Este módulo es responsable de interrogar periódicamente al sistema operativo Linux sobre el uso de recursos. Extrae:
*   **CPU**: Porcentaje de uso actual (usando `/proc/stat` o `psutil`).
*   **Temperatura**: Temperatura del CPU (usando `/sys/class/thermal/thermal_zone0/temp`).
*   **RAM**: Porcentaje de memoria utilizada (usando `/proc/meminfo` o `psutil`).
*   **Disco**: Porcentaje de espacio en disco de la partición raíz `/`.
*   **Red**: Dirección IP actual en la interfaz principal (por ejemplo, `wlan0` o `eth0`).
*   **Uptime**: Tiempo total de actividad del sistema.

### `src/weather.py`
Para mantener el sistema independiente de claves API externas que puedan expirar o requerir suscripciones, este módulo utiliza la API pública y gratuita de **Open-Meteo**.
*   **Parámetros**: Coordenadas de latitud/longitud (configurables a través de variables de entorno).
*   **Respuesta**: Temperatura actual, velocidad del viento y código de clima (WMO code) mapeado a una cadena legible (ej. "Despejado", "Lluvia ligera").

---

## 2. Renderizado de Interfaz (`src/renderer.py`)

La resolución física de la pantalla es de **296 x 128 píxeles**. Utilizaremos la librería `Pillow` (PIL) para construir la imagen en memoria usando un buffer monocromático (`1-bit`).

### Estrategia de Orientación y Rotación
La pantalla nativa es vertical (128x296). Para visualizar la información de forma más natural, utilizaremos la orientación **horizontal** (296x128).
*   El lienzo de dibujo se inicializará con dimensiones 296x128.
*   Al pasar la imagen al driver, el método `getbuffer` se encargará de rotar la matriz de píxeles a la disposición física vertical que espera el controlador SSD1680.

### Distribución de la Pantalla (Layout)
La interfaz se organiza en zonas lógicas para maximizar la legibilidad:

```
+-------------------------------------------------------------+
| [Icon] Lunes, 06 de Julio - 00:54                           | <-- Header (Fecha, Hora)
+-------------------------------+-----------------------------+
| Clima:                        | CPU: 12%      RAM: 45%      |
| 18.5 °C                       | Disk: 24%     Temp: 42°C    | <-- Cuerpo Principal
| Despejado                     | IP: 192.168.1.100           |
+-------------------------------+-----------------------------+
| Alerta / Mensaje API: [Texto enviado por API]               | <-- Footer (Mensajes/API)
+-------------------------------------------------------------+
```

---

## 3. Endpoints de la API (`src/api.py`)

El servidor FastAPI expone los siguientes endpoints para su interacción con otras aplicaciones del ecosistema:

1.  `POST /api/message`
    *   **Propósito**: Mostrar un mensaje personalizado en la sección del Footer de la pantalla.
    *   **Payload (JSON)**: `{"text": "Mi mensaje personalizado", "duration": 60}`
    *   **Comportamiento**: Sobrescribe el texto del footer y despierta el loop de renderizado inmediatamente. Si se especifica `duration` (en segundos), el mensaje expirará después de ese tiempo y volverá a mostrar la información habitual del sistema.

2.  `POST /api/clear`
    *   **Propósito**: Borrar el mensaje personalizado actual.
    *   **Payload**: Ninguno.
    *   **Comportamiento**: Limpia el footer y redibuja la pantalla de inmediato.

3.  `POST /api/refresh`
    *   **Propósito**: Forzar la actualización inmediata de la pantalla con datos de clima y sistema actualizados.
    *   **Payload**: Ninguno.

4.  `GET /api/status`
    *   **Propósito**: Obtener el estado actual del daemon.
    *   **Respuesta**: Información del sistema, clima actual almacenado en caché, y el mensaje personalizado activo si existe.

---

## 4. Estrategia de Refresco de Pantalla

Las pantallas e-Paper tienen un tiempo de respuesta lento y sufren de degradación si se refrescan constantemente de forma completa (parpadeo blanco/negro).

1.  **Refresco Periódico de Fondo**:
    *   Cada **60 segundos** el loop del daemon actualizará la hora, las métricas del sistema y (opcionalmente cada 15-30 minutos) los datos del clima.
    *   Se utilizará **refresco parcial** (`display_Partial`) para estas actualizaciones minuto a minuto. Esto evita el parpadeo molesto y actualiza la pantalla en menos de 1 segundo.
2.  **Refresco Completo de Mantenimiento**:
    *   Cada **30 refrescos parciales** (aproximadamente cada 30 minutos) o al iniciar el daemon, se realizará un **refresco completo** (`display` y `Clear`) para remover fantasmas visuales (ghosting) y mantener la salud física del panel e-ink.
3.  **Manejo de Deep Sleep**:
    *   El driver llamará al comando `sleep` en el controlador SSD1680 después de cada actualización de pantalla para reducir el consumo a prácticamente 0 Watts entre actualizaciones.
