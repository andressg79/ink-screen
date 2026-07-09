# Ink Screen 📟

Servicio API y demonio en segundo plano diseñado para controlar una pantalla de tinta electrónica (E-Ink) **Waveshare de 2.9 pulgadas V2** conectada a una Orange Pi (o Raspberry Pi). El servicio muestra métricas en tiempo real del sistema, información del clima local y permite enviar mensajes personalizados de forma remota a través de una API web rápida construida con FastAPI.

---

## 🚀 Características

*   **Métricas del Sistema**: Visualización en pantalla de temperatura de CPU, uso de CPU y memoria RAM, espacio en disco, tiempo de actividad (uptime) e IP local.
*   **Información del Clima**: Integración con un servicio de clima que actualiza la temperatura exterior periódicamente.
*   **Mensajes Personalizados**: Endpoint API para mostrar mensajes temporales configurables con tiempo de expiración.
*   **Ciclos de Refresco Optimizados**:
    *   Soporte para refrescos parciales rápidos.
    *   Refrescos completos periódicos automatizados para prevenir el efecto "ghosting" de la pantalla.
*   **Modo de Previsualización Local (Mock)**: Permite ejecutar y probar la renderización de la pantalla localmente sin hardware conectado, guardando la imagen generada en un archivo PNG para revisión visual rápida.

---

## 🔌 Conexiones de Hardware (Wiring)

Para conectar la pantalla Waveshare 2.9" V2 a tu Orange Pi (utilizando el bus SPI), sigue la siguiente tabla de conexiones de referencia (para más detalles, consulta [docs/wiring.md](docs/wiring.md)):

| EPD Pin | Nombre de Pin | Orange Pi Pin | Descripción |
| :--- | :--- | :--- | :--- |
| **VCC** | 3.3V | Pin 1 / 17 | Alimentación de 3.3V |
| **GND** | GND | Pin 9 / 14 / 25 | Tierra |
| **DIN** | MOSI | Pin 19 (SPI0_MOSI) | Entrada de datos SPI |
| **CLK** | SCLK | Pin 23 (SPI0_SCLK) | Reloj SPI |
| **CS** | CS | Pin 24 (SPI0_CS0) | Chip Select (activo bajo) |
| **DC** | Data/Command | Pin 22 (GPIO) | Selección de Datos/Comando |
| **RST** | Reset | Pin 18 (GPIO) | Reinicio de pantalla (activo bajo) |
| **BUSY** | Busy | Pin 16 (GPIO) | Indicador de pantalla ocupada |

---

## 🛠️ Configuración y Ejecución Local

### 1. Requisitos previos
Asegúrate de tener instalado Python 3.9 o superior y `pip` en tu máquina de desarrollo.

### 2. Configurar entorno virtual local
Para preparar el entorno local e instalar las dependencias de desarrollo y testing, ejecuta:
```bash
make setup-local
```
Activa el entorno virtual con:
```bash
source venv/bin/activate
```

### 3. Ejecutar en modo previsualización (MOCK)
Puedes simular el comportamiento de la pantalla localmente. La aplicación creará un servidor FastAPI en el puerto `8000` y guardará la previsualización de la pantalla en `/tmp/ink_screen_preview.png`:
```bash
make run-local
```

### 4. Pruebas Unitarias
Para correr los tests definidos en el directorio `tests/`:
```bash
make test
```

---

## 🚢 Despliegue en el Dispositivo (Orange Pi)

El despliegue está automatizado usando el comando `make`. Asegúrate de que las opciones del dispositivo remoto en el [Makefile](Makefile) coincidan con las de tu Orange Pi (`REMOTE_USER`, `REMOTE_HOST`, etc.).

1.  **Configurar dependencias del sistema en el dispositivo remoto**:
    Instala librerías necesarias como `spidev` y dependencias de renderizado en el dispositivo:
    ```bash
    make deploy-setup
    ```
2.  **Sincronizar código e iniciar servicio**:
    Sincroniza el código fuente local con la Orange Pi y arranca/reinicia el servicio systemd:
    ```bash
    make deploy-start
    ```
3.  **Monitorear logs en tiempo real**:
    ```bash
    make deploy-logs
    ```
4.  **Detener servicio**:
    ```bash
    make deploy-stop
    ```

---

## 🌐 Endpoints de la API

Una vez iniciado el servidor, puedes acceder a la documentación interactiva en `http://localhost:8000/docs`.

*   **`GET /api/metrics`**: Obtiene las últimas métricas recopiladas del sistema y del clima.
*   **`POST /api/message`**: Envía un mensaje personalizado para mostrar en la pantalla.
    *   **Cuerpo (JSON)**:
        ```json
        {
          "text": "Hola Mundo",
          "duration_minutes": 10
        }
        ```
*   **`DELETE /api/message`**: Elimina el mensaje personalizado actual de la pantalla y vuelve a mostrar las métricas estándar del sistema.

---

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Para más detalles, consulta [LICENSE.md](LICENSE.md).
