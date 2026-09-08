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

        # 1. HEADER (Y: 0 -> 20)
        if toolkit.emoji_font_path:
            draw.text((6, 2), "⛏️", font=font_emoji_m, fill=0)
            draw.text((24, 2), "NODO MINERO XMRIG", font=font_m, fill=0)
        else:
            draw.text((6, 2), "[MINERO XMRIG]", font=font_m, fill=0)

        status_text = miner_metrics.get("status", "OFFLINE").upper()
        soc_temp = system_metrics.get("temp", 0.0)
        temp_str = f"{soc_temp}°C"

        temp_width = draw.textlength(temp_str, font=font_s)
        badge_w = int(draw.textlength(f" {status_text} ", font=font_s)) + 4

        temp_x = WIDTH - temp_width - 8
        emoji_temp_w = 0
        if toolkit.emoji_font_path:
            emoji_temp_w = draw.textlength("🌡️", font=font_emoji_s)
            draw.text((temp_x - emoji_temp_w - 2, 4), "🌡️", font=font_emoji_s, fill=0)
        draw.text((temp_x, 4), temp_str, font=font_s, fill=0)

        badge_x = temp_x - (emoji_temp_w + 2 if toolkit.emoji_font_path else 0) - badge_w - 6
        if "MINANDO" in status_text:
            draw.rectangle([(badge_x, 2), (badge_x + badge_w, 16)], fill=0)
            draw.text((badge_x + 3, 3), status_text, font=font_s, fill=255)
        else:
            draw.rectangle([(badge_x, 2), (badge_x + badge_w, 16)], outline=0, width=1)
            draw.text((badge_x + 3, 3), status_text, font=font_s, fill=0)

        draw.line([(0, 18), (WIDTH, 18)], fill=0, width=1)

        # 2. BODY - TWO COLUMNS (Y: 19 -> 106)
        draw.line([(142, 18), (142, 106)], fill=0, width=1)

        # A. LEFT COLUMN: Hashrate (X: 0 -> 141)
        hr_10s = miner_metrics.get("hashrate_10s", 0.0)
        hr_60s = miner_metrics.get("hashrate_60s", 0.0)
        hr_max = miner_metrics.get("hashrate_max", 0.0)
        algo = miner_metrics.get("algo", "rx/0")
        threads = miner_metrics.get("threads", 8)
        hugepages = miner_metrics.get("hugepages", "100%")

        draw.text((6, 21), "HASH SPEED (10s):", font=font_s, fill=0)

        if status_text == "OFFLINE":
            draw.text((8, 35), "OFFLINE", font=font_l, fill=0)
        elif "PAUSADO" in status_text:
            draw.text((8, 35), "PAUSADO", font=font_l, fill=0)
        else:
            draw.text((8, 33), f"{hr_10s} H/s", font=font_l, fill=0)

        draw.text((6, 57), f"Max: {hr_max} H/s", font=font_s, fill=0)
        draw.text((6, 70), f"1m: {hr_60s} | Algo: {algo}", font=font_s, fill=0)
        draw.text((6, 85), f"CPU: {threads}t | HP: {hugepages}", font=font_s, fill=0)

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

        draw.text((146, 21), "RESULTADOS POOL:", font=font_s, fill=0)

        if toolkit.emoji_font_path:
            draw.text((146, 35), "📦", font=font_emoji_s, fill=0)
            draw.text((160, 35), f"Shares: {shares_good} ok / {shares_rej} rej", font=font_s, fill=0)
        else:
            draw.text((146, 35), f"Shares: {shares_good} ok / {shares_rej} rej", font=font_s, fill=0)

        draw.text((146, 50), f"Diff: {diff_str}", font=font_s, fill=0)
        draw.text((146, 65), f"Pool: {pool_display}", font=font_s, fill=0)

        if toolkit.emoji_font_path:
            draw.text((146, 80), "⏳", font=font_emoji_s, fill=0)
            draw.text((160, 80), f"Up: {uptime_str} | CPU: {cpu_sys}%", font=font_s, fill=0)
        else:
            draw.text((146, 80), f"Up: {uptime_str} | CPU: {cpu_sys}%", font=font_s, fill=0)

        # 3. FOOTER - INVERTED (Y: 107 -> 127)
        draw.rectangle([(0, 107), (WIDTH, HEIGHT)], fill=0)

        if custom_message:
            display_text = custom_message
            emoji_char = "📢"
        elif carousel_info and carousel_info.get("rotation_enabled") and carousel_info.get("total_screens", 1) > 1:
            idx = carousel_info.get("current_index", 2)
            tot = carousel_info.get("total_screens", 2)
            rem = carousel_info.get("time_remaining_sec", 0)
            next_name = carousel_info.get("next_title", "Sistema")
            display_text = f"[{idx}/{tot}] Sig: {next_name} en {rem}s"
            emoji_char = "🔄"
        else:
            display_text = f"XMRig RV2 | {pool_display}"
            emoji_char = "⛏️"

        max_len = 38 if toolkit.emoji_font_path else 46
        if len(display_text) > max_len:
            display_text = display_text[:max_len-3] + "..."

        if toolkit.emoji_font_path:
            draw.text((8, 111), emoji_char, font=font_emoji_m, fill=255)
            draw.text((8 + 18, 111), display_text, font=font_m, fill=255)
        else:
            draw.text((8, 111), display_text, font=font_m, fill=255)

        return img
