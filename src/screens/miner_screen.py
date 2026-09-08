import os
import logging
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw

from src.screens.base import BaseScreen, ScreenContext
from src.miner import get_miner_metrics
from src.system_info import get_all_metrics

logger = logging.getLogger(__name__)

WIDTH = 296
HEIGHT = 128

class MinerScreen(BaseScreen):
    """
    Módulo de visualización para el estado del minero XMRig y rendimiento del hardware.
    """
    name = "miner"
    title = "Nodo Minero XMRig"

    def __init__(self, duration: Optional[int] = None):
        dur = duration if duration is not None else int(os.getenv("SCREEN_MINER_DURATION", "30"))
        super().__init__(name=self.name, title=self.title, duration=dur)

    def fetch_data(self) -> Dict[str, Any]:
        """Recupera métricas del minero y del sistema."""
        miner_metrics = get_miner_metrics()
        system_metrics = get_all_metrics()
        return {
            "miner": miner_metrics,
            "system": system_metrics
        }

    def render(self, data: Dict[str, Any], toolkit: Any, context: ScreenContext) -> Image.Image:
        """Renderiza el dashboard del minero XMRig."""
        miner_metrics = data.get("miner", {})
        system_metrics = data.get("system", {})
        custom_message = context.custom_message
        carousel_info = context.carousel_info

        img = Image.new("1", (WIDTH, HEIGHT), 255)
        draw = ImageDraw.Draw(img)

        font_s = toolkit.get_font(10)
        font_m = toolkit.get_font(12)
        font_l = toolkit.get_font(20)
        font_emoji_s = toolkit.get_emoji_font(10)
        font_emoji_m = toolkit.get_emoji_font(12)

        # 1. HEADER ESTÁNDAR
        toolkit.draw_standard_header(draw, icon="⛏️", title="NODO MINERO XMRIG")

        # 2. BODY - DOS COLUMNAS (Y: 19 -> 127)
        draw.line([(142, 18), (142, 127)], fill=0, width=1)

        status_text = miner_metrics.get("status", "OFFLINE").upper()
        soc_temp = system_metrics.get("temp", 0.0)
        temp_str = f"{soc_temp}°C"

        # A. LEFT COLUMN: Hashrate & Estado (X: 0 -> 141)
        hr_10s = miner_metrics.get("hashrate_10s", 0.0)
        hr_60s = miner_metrics.get("hashrate_60s", 0.0)
        hr_max = miner_metrics.get("hashrate_max", 0.0)
        algo = miner_metrics.get("algo", "rx/0")
        threads = miner_metrics.get("threads", 8)
        hugepages = miner_metrics.get("hugepages", "100%")

        draw.text((6, 22), "HASH SPEED (10s):", font=font_s, fill=0)

        if status_text == "OFFLINE":
            draw.text((8, 35), "OFFLINE", font=font_l, fill=0)
        elif "PAUSADO" in status_text:
            draw.text((8, 35), "PAUSADO", font=font_l, fill=0)
        else:
            draw.text((8, 34), f"{hr_10s} H/s", font=font_l, fill=0)

        # Estado (Badge) y Temperatura
        badge_w = int(draw.textlength(f" {status_text} ", font=font_s)) + 2
        badge_h = 13
        if "MINANDO" in status_text:
            draw.rectangle([(6, 58), (6 + badge_w, 58 + badge_h)], fill=0)
            draw.text((8, 59), status_text, font=font_s, fill=255)
        else:
            draw.rectangle([(6, 58), (6 + badge_w, 58 + badge_h)], outline=0, width=1)
            draw.text((8, 59), status_text, font=font_s, fill=0)

        temp_x = 6 + badge_w + 6
        if toolkit.emoji_font_path:
            draw.text((temp_x, 58), "🌡️", font=font_emoji_s, fill=0)
            draw.text((temp_x + 13, 59), temp_str, font=font_s, fill=0)
        else:
            draw.text((temp_x, 59), temp_str, font=font_s, fill=0)

        draw.text((6, 75), f"Max: {hr_max} H/s", font=font_s, fill=0)
        draw.text((6, 91), f"1m: {hr_60s} | Algo: {algo}", font=font_s, fill=0)
        draw.text((6, 107), f"CPU: {threads}t | HP: {hugepages}", font=font_s, fill=0)

        # B. RIGHT COLUMN: Pool Stats (X: 144 -> 295)
        shares_good = miner_metrics.get("shares_good", 0)
        shares_rej = miner_metrics.get("shares_rejected", 0)
        diff_str = miner_metrics.get("diff_formatted", "---")
        pool = miner_metrics.get("pool", "Desconocido")
        uptime_str = miner_metrics.get("uptime", "---")
        cpu_sys = system_metrics.get("cpu", 0.0)

        if "moneroocean" in pool.lower():
            pool_display = "MoneroOcean (TLS)"
        else:
            pool_display = pool.split(":")[0][:18]

        draw.text((146, 22), "RESULTADOS POOL:", font=font_s, fill=0)

        if toolkit.emoji_font_path:
            draw.text((146, 37), "📦", font=font_emoji_s, fill=0)
            draw.text((160, 37), f"Shares: {shares_good} ok / {shares_rej} rej", font=font_s, fill=0)
        else:
            draw.text((146, 37), f"Shares: {shares_good} ok / {shares_rej} rej", font=font_s, fill=0)

        draw.text((146, 55), f"Diff: {diff_str}", font=font_s, fill=0)
        draw.text((146, 73), f"Pool: {pool_display}", font=font_s, fill=0)

        if toolkit.emoji_font_path:
            draw.text((146, 91), "⏳", font=font_emoji_s, fill=0)
            draw.text((160, 91), f"Up: {uptime_str}", font=font_s, fill=0)
        else:
            draw.text((146, 91), f"Up: {uptime_str}", font=font_s, fill=0)

        draw.text((146, 107), f"CPU: {cpu_sys}%", font=font_s, fill=0)

        return img
