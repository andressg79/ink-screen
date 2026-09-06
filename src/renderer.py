import os
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from src.pixel_art import get_pixel_art_image

logger = logging.getLogger(__name__)

# Resolution
WIDTH = 296
HEIGHT = 128

class ScreenRenderer:
    def __init__(self):
        self.font_path = self._find_font()
        logger.info(f"Using font: {self.font_path or 'Pillow Default'}")
        
        # Configure timezone (defaults to America/Montevideo, Uruguay)
        from zoneinfo import ZoneInfo
        tz_name = os.environ.get("INK_SCREEN_TZ", "America/Montevideo")
        try:
            self.tz = ZoneInfo(tz_name)
            logger.info(f"ScreenRenderer timezone set to: {tz_name}")
        except Exception as e:
            logger.error(f"Failed to load timezone '{tz_name}', using local system timezone. Error: {e}")
            self.tz = None

        # Configure emoji font (Symbola)
        self.emoji_font_path = self._find_emoji_font()
        logger.info(f"Using emoji font: {self.emoji_font_path or 'None'}")

    def _find_font(self):
        # Candidates for standard fonts on Linux and macOS
        candidates = [
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            # macOS
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _find_emoji_font(self):
        # Symbola font paths (standard on Debian/Ubuntu)
        candidates = [
            "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",
            "/usr/share/fonts/truetype/ancient-scripts/Symbola.ttf",
            "/usr/share/fonts/truetype/symbola/Symbola.ttf",
            "/usr/share/fonts/truetype/symbola/Symbola_hint.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def get_font(self, size):
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except Exception as e:
                logger.error(f"Failed to load TrueType font: {e}")
        return ImageFont.load_default()

    def get_emoji_font(self, size):
        if self.emoji_font_path:
            try:
                return ImageFont.truetype(self.emoji_font_path, size)
            except Exception as e:
                logger.error(f"Failed to load Symbola emoji font: {e}")
        return self.get_font(size)

    def render(self, system_metrics: dict, weather_metrics: dict, custom_message: str = None, alert: dict = None) -> Image.Image:
        if alert:
            return self.render_alert(
                title=alert.get("title", ""),
                text=alert.get("text", ""),
                avatar=alert.get("avatar", "paisano"),
                footer=alert.get("footer")
            )

        # Create a new white image (1-bit mode: '1')
        img = Image.new("1", (WIDTH, HEIGHT), 255)
        draw = ImageDraw.Draw(img)

        # Load fonts at various sizes
        font_s = self.get_font(10)
        font_m = self.get_font(12)
        font_l = self.get_font(24)

        # -------------------------------------------------------------
        # 1. HEADER (Y: 0 -> 20)
        # -------------------------------------------------------------
        if self.tz:
            now = datetime.now(self.tz)
        else:
            now = datetime.now()
            
        date_str = now.strftime("%A, %d de %B")
        
        # Translate month and day names (case-insensitive to support varying locales)
        months_es = {
            "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
            "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
            "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
        }
        days_es = {
            "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles", "Thursday": "Jueves",
            "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
        }
        
        # Replace months
        for en, es in months_es.items():
            date_str = date_str.replace(en, es)
            date_str = date_str.replace(en.lower(), es)
            date_str = date_str.replace(en.upper(), es)
            
        # Replace days
        for en, es in days_es.items():
            date_str = date_str.replace(en, es)
            date_str = date_str.replace(en.lower(), es)
            date_str = date_str.replace(en.upper(), es)

        # Capitalize the first letter (e.g. "Martes, 07 de Julio")
        if date_str:
            date_str = date_str[0].upper() + date_str[1:]

        time_str = now.strftime("%H:%M")

        # Load emoji font at size 12 and 24
        font_emoji_m = self.get_emoji_font(12)
        font_emoji_l = self.get_emoji_font(24)

        # Draw Date (Left-aligned)
        if self.emoji_font_path:
            draw.text((6, 2), "📅", font=font_emoji_m, fill=0)
            date_x = 24
        else:
            date_x = 6
        draw.text((date_x, 2), date_str, font=font_m, fill=0)
        
        # Draw Time (Right-aligned using dynamic text length)
        time_width = draw.textlength(time_str, font=font_m)
        if self.emoji_font_path:
            emoji_width = draw.textlength("⏰", font=font_emoji_m)
            combined_width = emoji_width + 4 + time_width
            time_x = WIDTH - combined_width - 8
            draw.text((time_x, 2), "⏰", font=font_emoji_m, fill=0)
            draw.text((time_x + emoji_width + 4, 2), time_str, font=font_m, fill=0)
        else:
            time_x = WIDTH - time_width - 8
            draw.text((time_x, 2), time_str, font=font_m, fill=0)

        # Header dividing line
        draw.line([(0, 18), (WIDTH, 18)], fill=0, width=1)

        # -------------------------------------------------------------
        # 2. BODY - TWO COLUMNS (Y: 19 -> 106)
        # -------------------------------------------------------------
        # Vertical divider line at X=135 (moved left to give right column more space)
        draw.line([(135, 18), (135, 106)], fill=0, width=1)

        # A. LEFT COLUMN: Weather Info (X: 0 -> 134)
        temp = weather_metrics.get("temp", "--.-")
        condition = weather_metrics.get("condition", "Cargando...")
        humidity = weather_metrics.get("humidity", "--")
        wind = weather_metrics.get("wind", "--")
        icon = weather_metrics.get("icon", "")
        
        # Make wind string compact (e.g. "6.3 km/h" -> "6km/h")
        try:
            wind_val = wind.replace(" km/h", "").strip()
            wind_compact = f"{round(float(wind_val))}km/h"
        except Exception:
            wind_compact = wind.replace(" km/h", "km/h").strip()

        draw.text((6, 22), "Montevideo", font=font_m, fill=0)
        draw.text((8, 38), f"{temp}°C", font=font_l, fill=0)
        
        # Draw weather icon next to the temperature if Symbola font is available
        if self.emoji_font_path and icon:
            temp_width = draw.textlength(f"{temp}°C", font=font_l)
            draw.text((8 + temp_width + 8, 38), icon, font=font_emoji_l, fill=0)
        
        # Truncate weather condition if it's too long
        if len(condition) > 22:
            condition = condition[:19] + "..."
        draw.text((6, 70), condition, font=font_s, fill=0)
        
        # Draw humidity and wind on the same line (Y=86) with dynamic icons
        if self.emoji_font_path:
            draw.text((6, 86), "💧", font=font_emoji_m, fill=0)
            draw.text((6 + 14, 86), humidity, font=font_s, fill=0)
            
            hum_width = draw.textlength(humidity, font=font_s)
            wind_x = 6 + 14 + hum_width + 12
            
            draw.text((wind_x - 6, 86), "|", font=font_s, fill=0)
            draw.text((wind_x + 6, 86), "💨", font=font_emoji_m, fill=0)
            draw.text((wind_x + 6 + 14, 86), wind_compact, font=font_s, fill=0)
        else:
            draw.text((6, 86), f"Hum: {humidity} | Vto: {wind_compact}", font=font_s, fill=0)

        # B. RIGHT COLUMN: System Info (X: 136 -> 295)
        cpu = system_metrics.get("cpu", 0.0)
        temp_c = system_metrics.get("temp", 0.0)
        ram = system_metrics.get("ram", 0.0)
        disk = system_metrics.get("disk", 0.0)
        ip = system_metrics.get("ip", "127.0.0.1")
        uptime = system_metrics.get("uptime", "unknown")

        # Repositioned system metrics to start at Y=22 with icons (Y = 22, 36, 50, 64, 78, 92)
        def draw_metric_line(y, icon_char, label):
            if self.emoji_font_path:
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

        # -------------------------------------------------------------
        # 3. FOOTER - INVERTED (Y: 107 -> 127)
        # -------------------------------------------------------------
        # Draw inverted footer rectangle (black background)
        draw.rectangle([(0, 107), (WIDTH, HEIGHT)], fill=0)

        if custom_message:
            display_text = custom_message
            emoji_char = "📢"
        else:
            display_text = "orangepirv2.local | Sistema Activo"
            emoji_char = "⚙️"

        # Truncate if footer text is too long
        max_len = 38 if self.emoji_font_path else 46
        if len(display_text) > max_len:
            display_text = display_text[:max_len-3] + "..."

        # Draw white text over black background
        if self.emoji_font_path:
            draw.text((8, 111), emoji_char, font=font_emoji_m, fill=255)
            draw.text((8 + 18, 111), display_text, font=font_m, fill=255)
        else:
            draw.text((8, 111), display_text, font=font_m, fill=255)

        return img

    def render_alert(self, title: str, text: str, avatar: str, footer: str = None) -> Image.Image:
        """
        Renders a full-screen alert message with a retro RPG textbox style.
        """
        # Create a new white image (1-bit mode: '1')
        img = Image.new("1", (WIDTH, HEIGHT), 255)
        draw = ImageDraw.Draw(img)

        # 1. RPG Double Border
        # Outer border (thick, 2px)
        draw.rectangle([(2, 2), (WIDTH - 3, HEIGHT - 3)], outline=0, width=2)
        # Inner border (thin, 1px)
        draw.rectangle([(6, 6), (WIDTH - 7, HEIGHT - 7)], outline=0, width=1)

        # Fonts
        font_s = self.get_font(10)
        font_m = self.get_font(12)

        # 2. Centered Title
        title_width = draw.textlength(title, font=font_m)
        title_x = (WIDTH - title_width) // 2
        draw.text((title_x, 10), title, font=font_m, fill=0)

        # Dividing line below title
        draw.line([(6, 26), (WIDTH - 7, 26)], fill=0, width=1)

        # 3. Portrait Frame & Sprite Paste (Left Column)
        # Frame outer box (11, 33) to (77, 99) -> 66x66 boundary
        draw.rectangle([(11, 33), (77, 99)], outline=0, width=1)

        try:
            # get_pixel_art_image now directly returns the pre-dithered 64x64 image
            sprite_img = get_pixel_art_image(avatar)
            img.paste(sprite_img, (12, 34))
        except Exception as e:
            logger.error(f"Error renderizando retrato RPG pixel art: {e}")

        # 4. Word-wrapped text (Right Column)
        # Space X: 84 to 284 (200 pixels width)
        # Y: 27 to 105 (78 pixels vertical space)
        def wrap_text(t: str, max_w: int) -> list[str]:
            words = t.split(" ")
            lines = []
            curr = []
            for w in words:
                test_line = " ".join(curr + [w])
                w_len = draw.textlength(test_line, font=font_m)
                if w_len <= max_w:
                    curr.append(w)
                else:
                    if curr:
                        lines.append(" ".join(curr))
                        curr = [w]
                    else:
                        lines.append(w)
                        curr = []
            if curr:
                lines.append(" ".join(curr))
            return lines

        wrapped_lines = wrap_text(text, 200)

        # Centering the text block vertically inside the body space (Y: 27 to 105)
        line_height = 14
        total_text_h = len(wrapped_lines) * line_height
        start_y = max(30, (78 - total_text_h) // 2 + 27)

        y_cursor = start_y
        for line in wrapped_lines:
            # Boundary check to prevent writing over the footer dividing line
            if y_cursor + line_height > 105:
                break
            draw.text((84, y_cursor), line, font=font_m, fill=0)
            y_cursor += line_height

        # 5. Footer area (Y: 105 -> 127)
        # Footer dividing line at Y=105
        draw.line([(6, 105), (WIDTH - 7, 105)], fill=0, width=1)

        # Inverted footer block (black background)
        # Stays inside the inner border at HEIGHT - 8 = 120
        draw.rectangle([(7, 106), (WIDTH - 8, 120)], fill=0)

        # Parse emoji and text for consistent rendering
        if not footer:
            emoji_char = "⌛"
            display_text = "[ ESPERANDO... ]"
        else:
            # If the first character is non-ASCII (like an emoji), separate it
            if len(footer) > 0 and ord(footer[0]) > 127:
                emoji_char = footer[0]
                display_text = footer[1:].strip()
            else:
                emoji_char = ""
                display_text = footer

        # Draw the footer elements
        if self.emoji_font_path and emoji_char:
            font_emoji_s = self.get_emoji_font(10)
            emoji_width = draw.textlength(emoji_char, font=font_emoji_s)
            text_width = draw.textlength(display_text, font=font_s)
            combined_width = emoji_width + 4 + text_width
            footer_x = (WIDTH - combined_width) // 2
            
            draw.text((footer_x, 108), emoji_char, font=font_emoji_s, fill=255)
            draw.text((footer_x + emoji_width + 4, 108), display_text, font=font_s, fill=255)
        else:
            # Fallback if no emoji font is installed or no emoji is present
            full_text = f"{emoji_char} {display_text}".strip()
            footer_width = draw.textlength(full_text, font=font_s)
            footer_x = (WIDTH - footer_width) // 2
            draw.text((footer_x, 108), full_text, font=font_s, fill=255)

        return img

if __name__ == "__main__":
    # Test rendering locally and save the preview
    renderer = ScreenRenderer()
    mock_system = {
        "cpu": 14.5,
        "temp": 42.1,
        "ram": 55.3,
        "disk": 22.8,
        "ip": "192.168.1.150",
        "uptime": "2d 5h 17m"
    }
    mock_weather = {
        "temp": "22.5",
        "condition": "Soleado",
        "icon": "☀️",
        "humidity": "45%",
        "wind": "12.5"
    }
    
    # Render default view
    img = renderer.render(mock_system, mock_weather)
    img.save("/tmp/test_default.png")
    print("Test default render saved to /tmp/test_default.png")
    
    # Render with custom API message
    img_msg = renderer.render(mock_system, mock_weather, "Alerta: Reinicio programado en 10 minutos!")
    img_msg.save("/tmp/test_message.png")
    print("Test message render saved to /tmp/test_message.png")

    # Render RPG alert message
    mock_alert = {
        "title": "Alerta de Sistema",
        "text": "Se ha detectado una anomalía en el reactor central. ¡Evacuar inmediatamente!",
        "avatar": "caballero",
        "footer": "⌛ [ ESPERANDO ACCION... ]"
    }
    img_alert = renderer.render(mock_system, mock_weather, alert=mock_alert)
    img_alert.save("/tmp/test_alert.png")
    print("Test RPG alert render saved to /tmp/test_alert.png")
