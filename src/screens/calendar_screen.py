import os
import logging
from typing import Optional, Dict, Any, List
from PIL import Image, ImageDraw

from src.screens.base import BaseScreen, ScreenContext
from src.calendar_service import CalendarService

logger = logging.getLogger(__name__)

WIDTH = 296
HEIGHT = 128

class CalendarScreen(BaseScreen):
    """
    Módulo de visualización Plug & Play para la agenda y próximas reuniones de Google Calendar.
    """
    name = "calendar"
    title = "Agenda de Reuniones"

    def __init__(self, duration: Optional[int] = None, config_path: str = "config/calendars.yaml"):
        dur = duration if duration is not None else int(os.getenv("SCREEN_CALENDAR_DURATION", "30"))
        super().__init__(name=self.name, title=self.title, duration=dur)
        self.service = CalendarService(config_path=config_path)

    def fetch_data(self) -> Dict[str, Any]:
        """Recupera los eventos próximos de todos los calendarios configurados."""
        events = self.service.get_upcoming_events()
        return {"events": events}

    def render(self, data: Dict[str, Any], toolkit: Any, context: ScreenContext) -> Image.Image:
        """Renderiza el tablero de reuniones con diseño adaptativo (0, 1-2 o 3-4 reuniones)."""
        events: List[Dict[str, Any]] = data.get("events", [])
        custom_message = context.custom_message
        carousel_info = context.carousel_info

        img = Image.new("1", (WIDTH, HEIGHT), 255)
        draw = ImageDraw.Draw(img)

        font_xs = toolkit.get_font(9)
        font_s = toolkit.get_font(10)
        font_m = toolkit.get_font(12)
        font_emoji_s = toolkit.get_emoji_font(10)
        font_emoji_m = toolkit.get_emoji_font(12)

        # -------------------------------------------------------------
        # 1. HEADER ESTÁNDAR
        toolkit.draw_standard_header(draw, icon="📅", title="AGENDA DE REUNIONES")

        # -------------------------------------------------------------
        # 2. BODY - ADAPTATIVE LAYOUT (Y: 19 -> 127)
        # -------------------------------------------------------------
        num_events = len(events)

        if num_events == 0:
            # Estado Vacío (Empty State)
            msg_main = "Sin reuniones próximas"
            msg_sub = "(Próximos días despejados)"
            w_main = draw.textlength(msg_main, font=font_m)
            w_sub = draw.textlength(msg_sub, font=font_s)

            if toolkit.emoji_font_path:
                draw.text(((WIDTH - 24) // 2, 40), "🎉", font=toolkit.get_emoji_font(20), fill=0)
            draw.text(((WIDTH - w_main) // 2, 68), msg_main, font=font_m, fill=0)
            draw.text(((WIDTH - w_sub) // 2, 88), msg_sub, font=font_s, fill=0)

        elif num_events <= 2:
            # Modo Tarjetas Espaciosas (1 o 2 reuniones)
            row_height = 50
            start_y = 24

            for i, ev in enumerate(events[:2]):
                current_y = start_y + (i * row_height)
                
                # Línea divisoria si hay 2 eventos
                if i > 0:
                    draw.line([(6, current_y - 4), (WIDTH - 6, current_y - 4)], fill=0, width=1)

                # A. Fila Superior: Estado / Horario / VC / Etiqueta
                badge_x = 6
                if ev.get("is_in_progress"):
                    badge_text = "EN CURSO"
                    bw = int(draw.textlength(badge_text, font=font_xs)) + 6
                    draw.rectangle([(badge_x, current_y), (badge_x + bw, current_y + 12)], fill=0)
                    draw.text((badge_x + 3, current_y + 1), badge_text, font=font_xs, fill=255)
                    time_x = badge_x + bw + 6
                else:
                    time_x = badge_x

                # Formato de horario
                if ev.get("is_today"):
                    time_text = f"{ev['start_str']} - {ev['end_str']}"
                else:
                    time_text = f"{ev['date_str']} {ev['start_str']} - {ev['end_str']}"

                draw.text((time_x, current_y), time_text, font=font_s, fill=0)
                time_end_x = time_x + int(draw.textlength(time_text, font=font_s))

                # Ícono de videollamada
                if ev.get("has_video_call"):
                    if toolkit.emoji_font_path:
                        draw.text((time_end_x + 5, current_y - 1), "📹", font=font_emoji_s, fill=0)
                    else:
                        draw.text((time_end_x + 5, current_y), "[VC]", font=font_xs, fill=0)

                # Etiqueta de calendario (a la derecha)
                label_text = f"[{ev.get('calendar_label', 'Cal')}]"
                label_w = draw.textlength(label_text, font=font_xs)
                draw.text((WIDTH - label_w - 8, current_y), label_text, font=font_xs, fill=0)

                # B. Fila Inferior: Título del evento
                summary = ev.get("summary", "Sin título")
                # Truncar título si excede el ancho disponible
                max_summary_len = 36
                if len(summary) > max_summary_len:
                    summary = summary[:max_summary_len - 3] + "..."
                draw.text((6, current_y + 18), summary, font=font_m, fill=0)

        else:
            # Modo Lista Compacta (3 o 4 reuniones)
            row_height = 26 if num_events >= 4 else 34
            start_y = 23

            for i, ev in enumerate(events[:4]):
                current_y = start_y + (i * row_height)

                # Viñeta de estado (● si está en curso, • si es futura)
                if ev.get("is_in_progress"):
                    indicator = "●"
                    if toolkit.emoji_font_path:
                        draw.text((6, current_y + 1), "🔴", font=toolkit.get_emoji_font(8), fill=0)
                    else:
                        draw.text((6, current_y), indicator, font=font_s, fill=0)
                else:
                    draw.text((6, current_y), "•", font=font_s, fill=0)

                # Horario compacto
                if ev.get("is_today"):
                    time_disp = ev["start_str"]
                else:
                    time_disp = f"{ev['date_str']} {ev['start_str']}"

                draw.text((16, current_y), time_disp, font=font_s, fill=0)
                time_w_ev = int(draw.textlength(time_disp, font=font_s))

                title_start_x = 16 + time_w_ev + 6

                # Videollamada
                if ev.get("has_video_call"):
                    if toolkit.emoji_font_path:
                        draw.text((title_start_x, current_y), "📹", font=font_emoji_s, fill=0)
                        title_start_x += 16
                    else:
                        draw.text((title_start_x, current_y), "v", font=font_xs, fill=0)
                        title_start_x += 10

                # Etiqueta derecha
                label_text = f"[{ev.get('calendar_label', '')}]"
                label_w = int(draw.textlength(label_text, font=font_xs))
                draw.text((WIDTH - label_w - 6, current_y + 1), label_text, font=font_xs, fill=0)

                # Título recortado dinámicamente según espacio disponible
                avail_w = (WIDTH - label_w - 10) - title_start_x
                summary = ev.get("summary", "Sin título")
                while draw.textlength(summary, font=font_s) > avail_w and len(summary) > 4:
                    summary = summary[:-4] + "..."
                draw.text((title_start_x, current_y), summary, font=font_s, fill=0)

        return img
