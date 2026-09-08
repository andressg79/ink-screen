import os
import re
import time
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo

import requests
import yaml
import icalendar
import recurring_ical_events

logger = logging.getLogger(__name__)

VC_PATTERNS = [
    r"meet\.google\.com",
    r"zoom\.us",
    r"teams\.microsoft\.com",
    r"teams\.live\.com",
    r"webex\.com"
]

class CalendarService:
    """
    Servicio de sincronización y normalización de eventos de calendario (iCal)
    compatible con múltiples cuentas y calendarios.
    """
    def __init__(self, config_path: str = "config/calendars.yaml"):
        self.config_path = config_path
        self.tz_name = os.getenv("INK_SCREEN_TZ", "America/Montevideo")
        try:
            self.tz = ZoneInfo(self.tz_name)
        except Exception:
            self.tz = None

        self.cached_events: List[Dict[str, Any]] = []
        self.last_fetch_time: float = 0.0

    def load_config(self) -> Dict[str, Any]:
        """Carga la configuración de calendarios con fallback seguro."""
        target_path = self.config_path
        if not os.path.exists(target_path):
            example_path = f"{self.config_path}.example"
            if os.path.exists(example_path):
                logger.info(f"Usando plantilla de configuración: {example_path}")
                target_path = example_path
            else:
                logger.warning(f"No se encontró archivo de configuración en {target_path}")
                return {"settings": {}, "calendars": []}

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data or {"settings": {}, "calendars": []}
        except Exception as e:
            logger.error(f"Error leyendo configuración de calendarios en {target_path}: {e}")
            return {"settings": {}, "calendars": []}

    def _normalize_dt(self, dt_val: Any) -> datetime:
        """Convierte una fecha o datetime a datetime consciente de zona horaria local."""
        if isinstance(dt_val, datetime):
            if dt_val.tzinfo is None:
                # Si no tiene zona horaria, asumimos UTC o local
                if self.tz:
                    return dt_val.replace(tzinfo=self.tz)
                return dt_val
            if self.tz:
                return dt_val.astimezone(self.tz)
            return dt_val
        elif isinstance(dt_val, date):
            # Evento de todo el día
            dt_combined = datetime.combine(dt_val, datetime.min.time())
            if self.tz:
                return dt_combined.replace(tzinfo=self.tz)
            return dt_combined
        # Fallback
        now_local = datetime.now(self.tz) if self.tz else datetime.now()
        return now_local

    def _detect_video_call(self, event: icalendar.Event) -> bool:
        """Determina si un evento tiene una reunión virtual (Meet, Zoom, Teams)."""
        desc = str(event.get("DESCRIPTION", "") or "")
        loc = str(event.get("LOCATION", "") or "")
        conf = str(event.get("X-GOOGLE-CONFERENCE", "") or "")
        combined = f"{desc} {loc} {conf}".lower()

        for pattern in VC_PATTERNS:
            if re.search(pattern, combined):
                return True
        return False

    def fetch_events_from_feed(self, cal_cfg: Dict[str, Any], window_start: datetime, window_end: datetime) -> List[Dict[str, Any]]:
        """Descarga y parsea un feed iCal individual."""
        url = cal_cfg.get("url")
        label = cal_cfg.get("label", "Calendario")
        account = cal_cfg.get("account", "Personal")

        if not url or not cal_cfg.get("enabled", True):
            return []

        try:
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            cal = icalendar.Calendar.from_ical(resp.content)
        except Exception as e:
            logger.error(f"Error descargando feed iCal '{label}' ({url}): {e}")
            return []

        parsed_events = []
        try:
            # Expande recurrencias (RRULE) dentro de la ventana dada
            expanded = recurring_ical_events.of(cal).between(window_start, window_end)
            now_local = datetime.now(self.tz) if self.tz else datetime.now()

            for ev in expanded:
                try:
                    dtstart_raw = ev.get("DTSTART")
                    if not dtstart_raw:
                        continue
                    start_dt = self._normalize_dt(dtstart_raw.dt)

                    dtend_raw = ev.get("DTEND")
                    if dtend_raw:
                        end_dt = self._normalize_dt(dtend_raw.dt)
                    else:
                        end_dt = start_dt + timedelta(hours=1)

                    # Descartar eventos ya concluidos
                    if end_dt < now_local:
                        continue

                    # Identificar si el evento está en curso
                    is_in_progress = (start_dt <= now_local <= end_dt)

                    summary = str(ev.get("SUMMARY", "Sin título") or "Sin título").strip()
                    has_vc = self._detect_video_call(ev)

                    parsed_events.append({
                        "summary": summary,
                        "start_time": start_dt,
                        "end_time": end_dt,
                        "start_str": start_dt.strftime("%H:%M"),
                        "end_str": end_dt.strftime("%H:%M"),
                        "date_str": start_dt.strftime("%d/%m"),
                        "is_today": (start_dt.date() == now_local.date()),
                        "is_in_progress": is_in_progress,
                        "has_video_call": has_vc,
                        "calendar_label": label,
                        "account": account,
                    })
                except Exception as parse_err:
                    logger.debug(f"Error parseando evento individual: {parse_err}")
                    continue

        except Exception as exp_err:
            logger.error(f"Error procesando recurrencias de iCal '{label}': {exp_err}")

        return parsed_events

    def get_upcoming_events(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Retorna la lista ordenada de próximas reuniones consolidadas
        desde todas las fuentes configuradas, con caché TTL.
        """
        config = self.load_config()
        settings = config.get("settings", {})
        cache_ttl = settings.get("cache_ttl_seconds", 300)
        max_events = settings.get("max_events", 4)

        now_ts = time.time()
        if self.cached_events and not force_refresh and (now_ts - self.last_fetch_time < cache_ttl):
            # Si hay caché válida, actualizamos únicamente el flag 'is_in_progress' con la hora actual
            now_local = datetime.now(self.tz) if self.tz else datetime.now()
            for ev in self.cached_events:
                ev["is_in_progress"] = (ev["start_time"] <= now_local <= ev["end_time"])
            # Descartar los que hayan concluido mientras dormía el worker
            valid_events = [ev for ev in self.cached_events if ev["end_time"] >= now_local]
            return valid_events[:max_events]

        now_local = datetime.now(self.tz) if self.tz else datetime.now()
        window_start = now_local - timedelta(hours=2)
        window_end = now_local + timedelta(days=7)

        all_events: List[Dict[str, Any]] = []
        calendars = config.get("calendars", [])

        for cal_cfg in calendars:
            cal_events = self.fetch_events_from_feed(cal_cfg, window_start, window_end)
            all_events.extend(cal_events)

        # Ordenar cronológicamente por hora de inicio
        all_events.sort(key=lambda x: x["start_time"])

        self.cached_events = all_events
        self.last_fetch_time = now_ts

        return self.cached_events[:max_events]
