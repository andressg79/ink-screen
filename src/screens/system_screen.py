import os
import time
import logging
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw

from src.screens.base import BaseScreen, ScreenContext
from src.system_info import get_all_metrics
from src.weather import WeatherService

logger = logging.getLogger(__name__)

WIDTH = 296
HEIGHT = 128

class SystemScreen(BaseScreen):
    """
    Módulo de visualización para el estado del sistema y el clima local.
    """
    name = "system"
    title = "Sistema y Clima"

    def __init__(self, duration: Optional[int] = None):
        dur = duration if duration is not None else int(os.getenv("SCREEN_SYSTEM_DURATION", "60"))
        super().__init__(name=self.name, title=self.title, duration=dur)
        self.weather_service = WeatherService()
        self.weather_interval = 900  # 15 minutos en segundos
        self.last_weather_fetch = 0.0
        self.cached_weather: Dict[str, Any] = {}

    def fetch_data(self) -> Dict[str, Any]:
        """Recupera métricas del sistema y del clima con caché interna de 15 min."""
        now = time.time()
        if not self.cached_weather or (now - self.last_weather_fetch >= self.weather_interval):
            try:
                self.cached_weather = self.weather_service.fetch_weather()
                self.last_weather_fetch = now
            except Exception as e:
                logger.error(f"Error actualizando clima en SystemScreen: {e}")

        system_metrics = get_all_metrics()
        return {
            "system": system_metrics,
            "weather": self.cached_weather
        }

    def render(self, data: Dict[str, Any], toolkit: Any, context: ScreenContext) -> Image.Image:
        """Renderiza la pantalla de Sistema y Clima."""
        system_metrics = data.get("system", {})
        weather_metrics = data.get("weather", {})
        custom_message = context.custom_message
        carousel_info = context.carousel_info

        img = Image.new("1", (WIDTH, HEIGHT), 255)
        draw = ImageDraw.Draw(img)

        font_s = toolkit.get_font(10)
        font_m = toolkit.get_font(12)
        font_l = toolkit.get_font(20)
        font_emoji_s = toolkit.get_emoji_font(10)
        font_emoji_m = toolkit.get_emoji_font(12)
        font_emoji_l = toolkit.get_emoji_font(20)

        # 1. HEADER ESTÁNDAR
        now_dt = toolkit.get_now()
        date_str = now_dt.strftime("%A, %d de %B")

        months_es = {
            "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
            "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
            "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
        }
        days_es = {
            "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles", "Thursday": "Jueves",
            "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
        }
        for en, es in months_es.items():
            date_str = date_str.replace(en, es).replace(en.lower(), es).replace(en.upper(), es)
        for en, es in days_es.items():
            date_str = date_str.replace(en, es).replace(en.lower(), es).replace(en.upper(), es)
        if date_str:
            date_str = date_str[0].upper() + date_str[1:]

        time_str = now_dt.strftime("%H:%M")
        toolkit.draw_standard_header(draw, icon="📅", title=date_str, time_str=time_str)

        # 2. BODY - DOS COLUMNAS (Y: 19 -> 127)
        draw.line([(135, 18), (135, 127)], fill=0, width=1)

        # A. LEFT COLUMN: Clima (X: 0 -> 134)
        temp = weather_metrics.get("temp", "--.-")
        condition = weather_metrics.get("condition", "Cargando...")
        humidity = weather_metrics.get("humidity", "--")
        wind = weather_metrics.get("wind", "--")
        icon = weather_metrics.get("icon", "")

        try:
            wind_val = wind.replace(" km/h", "").strip()
            wind_compact = f"{round(float(wind_val))}km/h"
        except Exception:
            wind_compact = wind.replace(" km/h", "km/h").strip()

        draw.text((6, 23), "Montevideo", font=font_m, fill=0)
        draw.text((8, 41), f"{temp}°C", font=font_l, fill=0)

        if toolkit.emoji_font_path and icon:
            temp_width = draw.textlength(f"{temp}°C", font=font_l)
            draw.text((8 + temp_width + 8, 41), icon, font=font_emoji_l, fill=0)

        if len(condition) > 22:
            condition = condition[:19] + "..."
        draw.text((6, 73), condition, font=font_s, fill=0)

        if toolkit.emoji_font_path:
            draw.text((6, 93), "💧", font=font_emoji_m, fill=0)
            draw.text((6 + 14, 93), humidity, font=font_s, fill=0)

            hum_width = draw.textlength(humidity, font=font_s)
            wind_x = 6 + 14 + hum_width + 12

            draw.text((wind_x - 6, 93), "|", font=font_s, fill=0)
            draw.text((wind_x + 6, 93), "💨", font=font_emoji_m, fill=0)
            draw.text((wind_x + 6 + 14, 93), wind_compact, font=font_s, fill=0)
        else:
            draw.text((6, 93), f"Hum: {humidity} | Vto: {wind_compact}", font=font_s, fill=0)

        # B. RIGHT COLUMN: Métricas del Sistema (X: 136 -> 295)
        cpu = system_metrics.get("cpu", 0.0)
        temp_c = system_metrics.get("temp", 0.0)
        ram = system_metrics.get("ram", 0.0)
        disk = system_metrics.get("disk", 0.0)
        ip = system_metrics.get("ip", "127.0.0.1")
        uptime = system_metrics.get("uptime", "unknown")

        def draw_metric_line(y, icon_char, label):
            if toolkit.emoji_font_path:
                draw.text((142, y), icon_char, font=font_emoji_m, fill=0)
                draw.text((142 + 16, y), label, font=font_s, fill=0)
            else:
                draw.text((142, y), label, font=font_s, fill=0)

        draw_metric_line(23, "⚙️", f"CPU: {cpu}%")
        draw_metric_line(40, "🌡️", f"Temp: {temp_c}°C")
        draw_metric_line(57, "📊", f"RAM: {ram}%")
        draw_metric_line(74, "💾", f"Disco: {disk}%")
        draw_metric_line(91, "🌐", f"IP: {ip}")
        draw_metric_line(108, "⏳", f"Uptime: {uptime}")

        return img
