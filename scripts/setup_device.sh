#!/usr/bin/env bash
# Script de configuración del dispositivo para Orange Pi RV2
# Debe ejecutarse con privilegios sudo en la Orange Pi.

set -euo pipefail

echo "===================================================="
echo " Iniciando Configuración del Dispositivo (Orange Pi)"
echo "===================================================="

# 1. Instalar paquetes de sistema requeridos
echo "Instalando paquetes del sistema..."
apt-get update
apt-get install -y \
    python3-venv \
    python3-pip \
    python3-spidev \
    python3-pil \
    gpiod \
    libgpiod-dev \
    rsync

# 2. Configurar reglas udev para acceso sin Root a SPI y GPIO
echo "Configurando reglas udev para acceso SPI y GPIO..."

# Regla SPI (grupo dialout)
cat <<EOF > /etc/udev/rules.d/99-spi.rules
SUBSYSTEM=="spidev", KERNEL=="spidev*", MODE="0660", GROUP="dialout"
EOF

# Regla GPIO (grupo dialout y recursividad en sysfs resolviendo symlinks)
cat <<EOF > /etc/udev/rules.d/99-gpio.rules
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", ACTION=="add", GROUP="dialout", MODE="0660"
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", ACTION=="add", PROGRAM="/bin/sh -c 'chown -R root:dialout /sys/class/gpio && chmod -R 770 /sys/class/gpio'"
SUBSYSTEM=="gpio", KERNEL=="gpio*", ACTION=="add", PROGRAM="/bin/sh -c 'chown -R root:dialout /sys/class/gpio/%k/ && chmod -R ug+rw /sys/class/gpio/%k/'"
EOF

# Aplicar las nuevas reglas udev inmediatamente
echo "Aplicando cambios de udev..."
udevadm control --reload-rules
udevadm trigger

# Asegurarse de que el usuario 'andres' esté en el grupo dialout (ya debería estar)
if id -nG andres | grep -qw dialout; then
    echo "El usuario 'andres' ya pertenece al grupo 'dialout'."
else
    echo "Agregando usuario 'andres' al grupo 'dialout'..."
    usermod -aG dialout andres
fi

# 3. Configurar entorno virtual de Python
echo "Configurando el entorno virtual de Python en la app..."
APP_DIR="/home/andres/ink-screen"

if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    # Crear virtual environment con acceso a paquetes del sistema (--system-site-packages)
    # Esto nos permite importar python3-spidev y python3-pil que ya están compilados para RISC-V.
    echo "Creando virtual env con --system-site-packages..."
    python3 -m venv --system-site-packages venv
    
    # Instalar FastAPI, Uvicorn y Requests (librerías pure-python) en el venv
    echo "Instalando FastAPI y dependencias en el venv..."
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install fastapi uvicorn requests
    
    # Restaurar propiedad del directorio de la aplicación al usuario andres
    echo "Restaurando propiedad de los archivos a 'andres'..."
    chown -R andres:andres "$APP_DIR"
else
    echo "Error: Directorio del proyecto no encontrado en $APP_DIR."
    echo "Por favor ejecute primero 'make deploy' desde la máquina local."
    exit 1
fi

# 4. Instalar el servicio systemd
echo "Instalando el servicio systemd..."
SERVICE_FILE="scripts/ink-screen.service"
if [ -f "$SERVICE_FILE" ]; then
    cp "$SERVICE_FILE" /etc/systemd/system/ink-screen.service
    systemctl daemon-reload
    systemctl enable ink-screen
    echo "Servicio systemd instalado y habilitado."
else
    echo "Advertencia: Archivo de servicio no encontrado en $SERVICE_FILE. Omite la instalación del servicio."
fi

echo "===================================================="
echo " Configuración Completada Exitosamente!"
echo " Si cambió de grupo, recuerde reiniciar sesión de SSH."
echo "===================================================="
