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

        # 1. HEADER (Y: 0 -> 18)
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

        if toolkit.emoji_font_path:
            draw.text((6, 2), "📅", font=font_emoji_m, fill=0)
            date_x = 24
        else:
            date_x = 6
        draw.text((date_x, 2), date_str, font=font_m, fill=0)

        time_width = draw.textlength(time_str, font=font_m)
        if toolkit.emoji_font_path:
            emoji_width = draw.textlength("⏰", font=font_emoji_m)
            combined_width = emoji_width + 4 + time_width
            time_x = WIDTH - combined_width - 8
            draw.text((time_x, 2), "⏰", font=font_emoji_m, fill=0)
            draw.text((time_x + emoji_width + 4, 2), time_str, font=font_m, fill=0)
        else:
            time_x = WIDTH - time_width - 8
            draw.text((time_x, 2), time_str, font=font_m, fill=0)

        draw.line([(0, 18), (WIDTH, 18)], fill=0, width=1)

        # 2. BODY - TWO COLUMNS (Y: 19 -> 106)
        draw.line([(135, 18), (135, 106)], fill=0, width=1)

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

        draw.text((6, 22), "Montevideo", font=font_m, fill=0)
        draw.text((8, 38), f"{temp}°C", font=font_l, fill=0)

        if toolkit.emoji_font_path and icon:
            temp_width = draw.textlength(f"{temp}°C", font=font_l)
            draw.text((8 + temp_width + 8, 38), icon, font=font_emoji_l, fill=0)

        if len(condition) > 22:
            condition = condition[:19] + "..."
        draw.text((6, 70), condition, font=font_s, fill=0)

        if toolkit.emoji_font_path:
            draw.text((6, 86), "💧", font=font_emoji_m, fill=0)
            draw.text((6 + 14, 86), humidity, font=font_s, fill=0)

            hum_width = draw.textlength(humidity, font=font_s)
            wind_x = 6 + 14 + hum_width + 12

            draw.text((wind_x - 6, 86), "|", font=font_s, fill=0)
            draw.text((wind_x + 6, 86), "💨", font=font_emoji_m, fill=0)
            draw.text((wind_x + 6 + 14, 86), wind_compact, font=font_s, fill=0)
        else:
            draw.text((6, 86), f"Hum: {humidity} | Vto: {wind_compact}", font=font_s, fill=0)

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

        draw_metric_line(22, "⚙️", f"CPU: {cpu}%")
        draw_metric_line(36, "🌡️", f"Temp: {temp_c}°C")
        draw_metric_line(50, "📊", f"RAM: {ram}%")
        draw_metric_line(64, "💾", f"Disco: {disk}%")
        draw_metric_line(78, "🌐", f"IP: {ip}")
        draw_metric_line(92, "⏳", f"Uptime: {uptime}")

        # 3. FOOTER - INVERTED (Y: 107 -> 127)
        draw.rectangle([(0, 107), (WIDTH, HEIGHT)], fill=0)

        if custom_message:
            display_text = custom_message
            emoji_char = "📢"
        elif carousel_info and carousel_info.get("rotation_enabled") and carousel_info.get("total_screens", 1) > 1:
            idx = carousel_info.get("current_index", 1)
            tot = carousel_info.get("total_screens", 2)
            rem = carousel_info.get("time_remaining_sec", 0)
            next_name = carousel_info.get("next_title", "Minero")
            display_text = f"[{idx}/{tot}] Sig: {next_name} en {rem}s"
            emoji_char = "🔄"
        else:
            display_text = "orangepirv2.local | Sistema Activo"
            emoji_char = "⚙️"

        max_len = 38 if toolkit.emoji_font_path else 46
        if len(display_text) > max_len:
            display_text = display_text[:max_len-3] + "..."

        if toolkit.emoji_font_path:
            draw.text((8, 111), emoji_char, font=font_emoji_m, fill=255)
            draw.text((8 + 18, 111), display_text, font=font_m, fill=255)
        else:
            draw.text((8, 111), display_text, font=font_m, fill=255)

        return img
