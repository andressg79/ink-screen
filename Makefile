# Configuración del Entorno y Despliegue Remoto

# Opciones remotas
REMOTE_USER = andres
REMOTE_HOST = orangepirv2.local
REMOTE_DIR = /home/andres/ink-screen
SSH_TARGET = $(REMOTE_USER)@$(REMOTE_HOST)

.PHONY: help setup-local run-local test deploy deploy-setup deploy-start deploy-stop deploy-status deploy-logs clean

help:
	@echo "Comandos disponibles:"
	@echo "  setup-local   - Configura el entorno virtual local e instala dependencias."
	@echo "  run-local     - Ejecuta la aplicación localmente en modo MOCK (guarda previsualización)."
	@echo "  test          - Ejecuta las pruebas unitarias locales."
	@echo "  deploy        - Sincroniza el código fuente con la Orange Pi por rsync/ssh."
	@echo "  deploy-setup  - Configura dependencias del sistema y udev en la Orange Pi (requiere sudo)."
	@echo "  deploy-start  - Sincroniza el código y arranca/reinicia el servicio en la Orange Pi."
	@echo "  deploy-stop   - Detiene el servicio en la Orange Pi."
	@echo "  deploy-status - Muestra el estado del servicio en la Orange Pi."
	@echo "  deploy-logs   - Muestra los logs en tiempo real del servicio en la Orange Pi."
	@echo "  clean         - Limpia archivos temporales y de caché de Python."

setup-local:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	@echo "Entorno local configurado. Ejecute 'source venv/bin/activate' para activarlo."

run-local:
	@echo "Iniciando aplicación en modo MOCK local..."
	INK_SCREEN_MOCK=1 ./venv/bin/python3 -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

test:
	PYTHONPATH=. ./venv/bin/pytest tests/

deploy:
	@echo "Sincronizando archivos con $(SSH_TARGET)..."
	ssh $(SSH_TARGET) "mkdir -p $(REMOTE_DIR)"
	rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.pytest_cache' --exclude 'reference' --exclude 'docs' --exclude '.git' ./ $(SSH_TARGET):$(REMOTE_DIR)/

deploy-setup:
	@echo "Instalando dependencias de sistema y configurando udev rules en el dispositivo..."
	ssh -t $(SSH_TARGET) "cd $(REMOTE_DIR) && chmod +x scripts/setup_device.sh && sudo ./scripts/setup_device.sh"

deploy-start: deploy
	@echo "Reiniciando el servicio ink-screen en el dispositivo..."
	ssh -t $(SSH_TARGET) "sudo systemctl daemon-reload && sudo systemctl enable ink-screen && sudo systemctl restart ink-screen"

deploy-stop:
	@echo "Deteniendo el servicio ink-screen en el dispositivo..."
	ssh -t $(SSH_TARGET) "sudo systemctl stop ink-screen"

deploy-status:
	ssh $(SSH_TARGET) "sudo systemctl status ink-screen"

deploy-logs:
	ssh -t $(SSH_TARGET) "journalctl -u ink-screen -f"

clean:
	rm -rf venv
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".eggs" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -f /tmp/ink_screen_preview.png
