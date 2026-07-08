import os
import sys
import time
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager

# Append root directory to sys.path to resolve 'src' packages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from fastapi import FastAPI

from src.api import router, state
from src.system_info import get_all_metrics
from src.weather import WeatherService
from src.renderer import ScreenRenderer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ink-screen.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("ink-screen")

# Initialize managers
weather_service = WeatherService()
renderer = ScreenRenderer()

# Constants
WEATHER_REFRESH_INTERVAL = 900  # 15 minutes in seconds
FULL_REFRESH_FREQUENCY = 30     # Perform full refresh every 30 updates

async def display_worker():
    """
    Background worker loop that manages e-ink screen refresh cycles.
    """
    logger.info("Iniciando display_worker daemon...")
    
    # Initialize the e-ink screen driver
    try:
        from src.driver.epd2in9_v2 import EPD
        epd = EPD()
        logger.info("Driver EPD cargado correctamente.")
    except Exception as e:
        logger.error(f"Error cargando el driver de la pantalla: {e}")
        return

    # Initial display clear and full refresh
    logger.info("Realizando inicialización de la pantalla...")
    try:
        epd.init()
        epd.Clear()
        epd.sleep()
    except Exception as e:
        logger.error(f"Error inicializando pantalla: {e}")

    last_weather_fetch = 0.0

    while True:
        try:
            # 1. Update weather data (with caching)
            now = time.time()
            if not state.weather_metrics or (now - last_weather_fetch >= WEATHER_REFRESH_INTERVAL):
                logger.info("Actualizando datos del clima...")
                state.weather_metrics = weather_service.fetch_weather()
                last_weather_fetch = now

            # 2. Update system metrics (always fresh)
            state.system_metrics = get_all_metrics()

            # 3. Check custom message expiry
            if state.custom_message_expiry:
                if now >= state.custom_message_expiry:
                    logger.info("El mensaje personalizado ha expirado. Limpiando...")
                    state.custom_message = None
                    state.custom_message_expiry = None

            # 4. Render image canvas
            logger.info("Renderizando nuevo lienzo de pantalla...")
            img = renderer.render(
                system_metrics=state.system_metrics,
                weather_metrics=state.weather_metrics,
                custom_message=state.custom_message
            )

            # 5. Push to physical display
            # Convert PIL image to 1-bit buffer
            image_buffer = epd.getbuffer(img)
            
            # Determine if we should perform a full refresh to prevent ghosting
            should_full_refresh = (state.refresh_count % FULL_REFRESH_FREQUENCY == 0)
            
            logger.info(f"Actualizando pantalla (Refresco: {'Completo' if should_full_refresh else 'Parcial'}, Nro: {state.refresh_count})...")
            
            # Wake up and write buffer
            if should_full_refresh:
                epd.init()
                epd.Clear()  # Flash black/white to clear ghosting
                epd.display_Base(image_buffer)
                epd.sleep()
                state.last_full_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                # EPD init_Fast is optimized for quick partial refresh cycles
                epd.init_Fast()
                epd.display_Partial(image_buffer, state.previous_image_buffer)
                epd.sleep()
                state.last_partial_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Save the current buffer as the previous one for the next partial update
            state.previous_image_buffer = image_buffer
            state.refresh_count += 1

        except Exception as e:
            logger.error(f"Error en el ciclo de actualización de pantalla: {e}")

        # 6. Wait for next refresh (60 seconds) or API trigger
        try:
            # Clear event in case it was set in a previous run
            state.force_refresh_event.clear()
            
            # If a custom message has an active timer, wake up exactly when it expires
            timeout = 60.0
            if state.custom_message_expiry:
                time_to_expiry = state.custom_message_expiry - time.time()
                if 0 < time_to_expiry < 60.0:
                    timeout = time_to_expiry

            logger.info(f"Display worker durmiendo por {timeout:.1f}s o hasta llamada de API...")
            await asyncio.wait_for(state.force_refresh_event.wait(), timeout=timeout)
            logger.info("Display worker despertado por señal de evento (API).")
        except asyncio.TimeoutError:
            # Standard timeout reached, perform routine refresh
            pass

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Startup
    worker_task = asyncio.create_task(display_worker())
    yield
    # Shutdown
    logger.info("Cancelando display worker...")
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    logger.info("Servidor apagado correctamente.")

# Create FastAPI application
app = FastAPI(
    title="Ink Screen API",
    description="API REST para controlar la pantalla E-Ink de la Orange Pi RV2",
    version="1.0.0",
    lifespan=app_lifespan
)

# Register API routes
app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Ink Screen REST API activa. Use /api/status para ver el estado o /docs para ver la documentación interactiva."}

if __name__ == "__main__":
    # If run directly, launch server
    port = int(os.environ.get("INK_SCREEN_PORT", "8000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=False)
