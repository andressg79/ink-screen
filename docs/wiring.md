# Conexiones de Hardware (Wiring)

Este documento describe la conexión física entre la placa **Orange Pi RV2 (cabezal de 26 pines)** y el módulo de pantalla **E-Ink ZJYE290S08W0G01 (2.9 pulgadas, 296x128 píxeles)**.

## Tabla de Conexiones de Pines

| Pin Físico Pantalla | Nombre Pin Pantalla | Pin Físico Orange Pi RV2 | Nombre Pin Orange Pi | Función | GPIO Linux (Sysfs) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | VCC | **Pin 1** | 3.3V | Alimentación de 3.3V | *N/A* |
| **2** | GND | **Pin 6** | GND | Tierra | *N/A* |
| **3** | DIN / SDI | **Pin 19** | SPI3_MOSI (SPI3_TXD) | Transmisión de datos SPI | *N/A (Manejado por SPI)* |
| **4** | CLK / SCK | **Pin 23** | SPI3_CLK | Reloj SPI | *N/A (Manejado por SPI)* |
| **5** | CS | **Pin 24** | SPI3_CS0 | Selección de chip SPI | *N/A (Manejado por SPI)* |
| **6** | DC | **Pin 22** | GPIO49 | Control de datos/comandos | **49** |
| **7** | RST | **Pin 11** | GPIO71 | Reinicio de hardware | **71** |
| **8** | BUSY | **Pin 13** | GPIO72 | Estado de pantalla (Busy) | **72** |

---

## Diagrama de Conexiones Físicas

A continuación se muestra el esquema del cabezal de 26 pines de la Orange Pi RV2 y cómo se conecta a la pantalla.

```
       Orange Pi RV2 Pin Header (26-pin)
      +---------------------------------+
(VCC) | [01] (3.3V)         (5.0V) [02] |
      | [03] (SDA)          (5.0V) [04] |
      | [05] (SCL)           (GND) [06] | (GND)
      | [07] (PWM9)         (GPIO) [08] |
      | [09] (GND)          (GPIO) [10] |
(RST) | [11] (GPIO71)       (GPIO) [12] |
(BUSY)| [13] (GPIO72)        (GND) [14] |
      | [15] (GPIO)         (GPIO) [16] |
      | [17] (3.3V)         (GPIO) [18] |
(DIN) | [19] (SPI3_MOSI)     (GND) [20] |
      | [21] (SPI3_MISO)    (GPIO) [22] | (DC)
(CLK) | [23] (SPI3_CLK)    (SPI_CS)[24] | (CS)
      | [25] (GND)          (GPIO) [26] |
      +---------------------------------+
```

---

## Configuración y Mapeo de Pines en Software

Para interactuar con la pantalla en Linux, se utiliza `/dev/spidev3.0` para SPI y el sistema de control `sysfs` en `/sys/class/gpio` para los pines GPIO (DC, RST, BUSY).

*   **SPI**:
    *   Archivo de dispositivo: `/dev/spidev3.0` (Bus SPI 3, Chip Select 0)
    *   Frecuencia máxima recomendada: `4 MHz` (4,000,000 Hz)
    *   Modo SPI: `0b00` (CPOL=0, CPHA=0)
*   **GPIOs**:
    *   **DC (Pin 22)** -> `/sys/class/gpio/gpio49`
    *   **RST (Pin 11)** -> `/sys/class/gpio/gpio71`
    *   **BUSY (Pin 13)** -> `/sys/class/gpio/gpio72`
