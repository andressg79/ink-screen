import os
import pytest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock
from PIL import Image

from src.calendar_service import CalendarService
from src.screens.calendar_screen import CalendarScreen
from src.screens.base import ScreenContext
from src.renderer import ScreenRenderer

def get_sample_ical() -> str:
    now_utc = datetime.now(timezone.utc)
    ev1_start = (now_utc + timedelta(hours=1)).strftime("%Y%m%dT%H%M%SZ")
    ev1_end = (now_utc + timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
    ev2_start = (now_utc + timedelta(hours=3)).strftime("%Y%m%dT%H%M%SZ")
    ev2_end = (now_utc + timedelta(hours=4)).strftime("%Y%m%dT%H%M%SZ")
    past_start = (now_utc - timedelta(days=2)).strftime("%Y%m%dT%H%M%SZ")
    past_end = (now_utc - timedelta(days=2, hours=-1)).strftime("%Y%m%dT%H%M%SZ")

    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
UID:event-1@example.com
DTSTART:{ev1_start}
DTEND:{ev1_end}
SUMMARY:Reunion de Planificacion
DESCRIPTION:Link de la llamada: https://meet.google.com/abc-defg-hij
LOCATION:Google Meet
STATUS:CONFIRMED
END:VEVENT
BEGIN:VEVENT
UID:event-2@example.com
DTSTART:{ev2_start}
DTEND:{ev2_end}
SUMMARY:Cafe con Colega
LOCATION:Oficina Central
STATUS:CONFIRMED
END:VEVENT
BEGIN:VEVENT
UID:event-past@example.com
DTSTART:{past_start}
DTEND:{past_end}
SUMMARY:Evento Pasado
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""

SAMPLE_RECURRING_ICAL = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test Recurring//EN
BEGIN:VEVENT
UID:recurring-daily@example.com
DTSTART:20260901T120000Z
DTEND:20260901T123000Z
RRULE:FREQ=DAILY
SUMMARY:Daily Standup Team
DESCRIPTION:Sala Zoom https://zoom.us/j/123456789
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""

def test_calendar_service_config_loading(tmp_path):
    # Test loading nonexistent config gracefully
    svc = CalendarService(config_path=str(tmp_path / "nonexistent.yaml"))
    cfg = svc.load_config()
    assert "calendars" in cfg

def test_calendar_service_parse_feed():
    svc = CalendarService()
    now_tz = datetime.now(svc.tz) if svc.tz else datetime.now()
    window_start = now_tz - timedelta(days=1)
    window_end = now_tz + timedelta(days=7)

    # Mock requests.get
    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.content = get_sample_ical().encode("utf-8")
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        cal_cfg = {
            "account": "Personal",
            "label": "TestCal",
            "url": "https://example.com/calendar.ics",
            "enabled": True
        }
        events = svc.fetch_events_from_feed(cal_cfg, window_start, window_end)

        # Should parse upcoming events and ignore past ones
        assert len(events) >= 1
        # Check video call detection on event 1
        ev_vc = next((e for e in events if "Planificacion" in e["summary"]), None)
        if ev_vc:
            assert ev_vc["has_video_call"] is True
            assert ev_vc["calendar_label"] == "TestCal"

def test_calendar_service_recurring_events():
    svc = CalendarService()
    now_tz = datetime.now(svc.tz) if svc.tz else datetime.now()
    window_start = now_tz - timedelta(hours=1)
    window_end = now_tz + timedelta(days=3)

    with patch("requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RECURRING_ICAL.encode("utf-8")
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        cal_cfg = {
            "account": "Trabajo",
            "label": "Work",
            "url": "https://example.com/recurring.ics",
            "enabled": True
        }
        events = svc.fetch_events_from_feed(cal_cfg, window_start, window_end)
        # Recurring event should expand to at least 1 or 2 occurrences in the window
        assert len(events) >= 1
        assert events[0]["has_video_call"] is True
        assert "Daily Standup" in events[0]["summary"]

def test_calendar_screen_render_empty():
    screen = CalendarScreen()
    renderer = ScreenRenderer()
    ctx = ScreenContext(carousel_info={"current_index": 3, "total_screens": 3, "rotation_enabled": True})

    img = screen.render({"events": []}, toolkit=renderer, context=ctx)
    assert isinstance(img, Image.Image)
    assert img.size == (296, 128)
    assert img.mode == "1"

def test_calendar_screen_render_spacious_cards():
    screen = CalendarScreen()
    renderer = ScreenRenderer()
    ctx = ScreenContext(carousel_info={"current_index": 3, "total_screens": 3, "rotation_enabled": True})

    events = [
        {
            "summary": "1:1 con Líder",
            "start_str": "10:00",
            "end_str": "10:30",
            "date_str": "08/09",
            "is_today": True,
            "is_in_progress": True,
            "has_video_call": True,
            "calendar_label": "Work"
        },
        {
            "summary": "Gimnasio",
            "start_str": "19:00",
            "end_str": "20:00",
            "date_str": "08/09",
            "is_today": True,
            "is_in_progress": False,
            "has_video_call": False,
            "calendar_label": "Personal"
        }
    ]
    img = screen.render({"events": events}, toolkit=renderer, context=ctx)
    assert isinstance(img, Image.Image)
    assert img.size == (296, 128)
    assert img.mode == "1"

def test_calendar_screen_render_compact_list():
    screen = CalendarScreen()
    renderer = ScreenRenderer()
    ctx = ScreenContext(carousel_info={"current_index": 3, "total_screens": 3, "rotation_enabled": True})

    events = [
        {"summary": "Daily", "start_str": "09:00", "end_str": "09:15", "date_str": "08/09", "is_today": True, "is_in_progress": True, "has_video_call": True, "calendar_label": "Work"},
        {"summary": "Sprint Review", "start_str": "11:00", "end_str": "12:00", "date_str": "08/09", "is_today": True, "is_in_progress": False, "has_video_call": True, "calendar_label": "Work"},
        {"summary": "Almuerzo", "start_str": "13:00", "end_str": "14:00", "date_str": "08/09", "is_today": True, "is_in_progress": False, "has_video_call": False, "calendar_label": "Personal"},
        {"summary": "Demo", "start_str": "16:00", "end_str": "17:00", "date_str": "08/09", "is_today": True, "is_in_progress": False, "has_video_call": True, "calendar_label": "Work"},
    ]
    img = screen.render({"events": events}, toolkit=renderer, context=ctx)
    assert isinstance(img, Image.Image)
    assert img.size == (296, 128)
    assert img.mode == "1"
