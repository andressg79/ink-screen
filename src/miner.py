import os
import sys
import time
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configuración por variables de entorno
XMRIG_API_URL = os.getenv("XMRIG_API_URL", "http://127.0.0.1:37988")
XMRIG_API_TOKEN = os.getenv("XMRIG_API_TOKEN", "f377144c0292734c501438e74a2e2fe87eec319ff76f1bc7f7d0224864c40c17")
XMRIG_TIMEOUT = float(os.getenv("XMRIG_TIMEOUT", "1.5"))

# Caché de última métrica válida
_LAST_VALID_METRICS: Optional[Dict[str, Any]] = None

def format_diff(diff: int) -> str:
    """Formatea la dificultad numérica en formato legible (ej: 1280169 -> 1.28M)"""
    if diff >= 1_000_000_000:
        return f"{diff / 1_000_000_000:.2f}G"
    elif diff >= 1_000_000:
        return f"{diff / 1_000_000:.2f}M"
    elif diff >= 1_000:
        return f"{diff / 1_000:.1f}K"
    return str(diff)

def format_uptime_seconds(seconds: int) -> str:
    """Formatea segundos en formato compacto (ej: 1d 4h 12m o 4h 12m o 35s)"""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours % 24 > 0 or days > 0:
        parts.append(f"{hours % 24}h")
    parts.append(f"{minutes % 60}m")
    return " ".join(parts)

def check_xmrig_process_state() -> Optional[str]:
    """
    Inspecciona /proc en Linux para verificar si el proceso xmrig existe y su estado.
    Retorna el estado de /proc/<pid>/status (ej: 'T' para pausado/stopped, 'S', 'R') o None si no existe.
    """
    if sys.platform != "linux":
        return None

    try:
        for entry in os.listdir("/proc"):
            if entry.isdigit():
                cmdline_path = os.path.join("/proc", entry, "cmdline")
                try:
                    with open(cmdline_path, "rb") as f:
                        cmd = f.read().decode("utf-8", errors="ignore")
                    if "xmrig" in cmd:
                        status_path = os.path.join("/proc", entry, "status")
                        with open(status_path, "r") as f:
                            for line in f:
                                if line.startswith("State:"):
                                    # Ej: "State:  T (stopped)" -> "T"
                                    state_char = line.split()[1]
                                    return state_char
                except Exception:
                    continue
    except Exception as e:
        logger.debug(f"Error inspeccionando /proc para xmrig: {e}")
    return None

def get_mock_miner_metrics() -> Dict[str, Any]:
    """Retorna métricas simuladas realistas para pruebas y desarrollo local."""
    return {
        "status": "MINANDO",
        "hashrate_10s": 124.5,
        "hashrate_60s": 121.0,
        "hashrate_15m": 118.2,
        "hashrate_max": 148.2,
        "shares_good": 42,
        "shares_total": 42,
        "shares_rejected": 0,
        "diff": 1280169,
        "diff_formatted": "1.28M",
        "pool": "gulf.moneroocean.stream:20128",
        "uptime": "4h 12m",
        "algo": "rx/0",
        "threads": 8,
        "hugepages": "100%",
        "paused": False,
        "raw_error": None
    }

def get_miner_metrics() -> Dict[str, Any]:
    """
    Obtiene las métricas actuales del minero XMRig consultando la API HTTP local.
    Si la API no responde, verifica si el watchdog lo pausó vía SIGSTOP.
    """
    global _LAST_VALID_METRICS

    # Modo Mock explícito
    if os.getenv("INK_SCREEN_MOCK") == "1":
        return get_mock_miner_metrics()

    headers = {}
    if XMRIG_API_TOKEN:
        headers["Authorization"] = f"Bearer {XMRIG_API_TOKEN}"

    url = f"{XMRIG_API_URL.rstrip('/')}/2/summary"

    try:
        resp = requests.get(url, headers=headers, timeout=XMRIG_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            
            # Hashrate
            hr_data = data.get("hashrate", {})
            total_hr = hr_data.get("total", [0.0, 0.0, 0.0]) or [0.0, 0.0, 0.0]
            hr_10s = round(float(total_hr[0] or 0.0), 1)
            hr_60s = round(float(total_hr[1] or 0.0), 1)
            hr_15m = round(float(total_hr[2] or 0.0), 1)
            hr_max = round(float(hr_data.get("highest") or 0.0), 1)

            # Results & Connection
            res_data = data.get("results", {})
            conn_data = data.get("connection", {})
            shares_good = res_data.get("shares_good", 0)
            shares_total = res_data.get("shares_total", 0)
            shares_rejected = conn_data.get("rejected", 0)
            diff = res_data.get("diff_current", 0)

            # Hugepages
            hp = data.get("hugepages", [0, 0])
            hp_str = f"{round((hp[0]/hp[1])*100)}%" if len(hp) >= 2 and hp[1] > 0 else "N/A"

            # Estado
            is_paused = data.get("paused", False)
            status_str = "PAUSADO" if is_paused else "MINANDO"

            uptime_sec = data.get("uptime", 0)
            uptime_str = format_uptime_seconds(uptime_sec)

            algo = data.get("algo", "rx/0")
            cpu_threads = data.get("cpu", {}).get("threads", 8)
            pool = conn_data.get("pool", "Desconocido")

            metrics = {
                "status": status_str,
                "hashrate_10s": hr_10s,
                "hashrate_60s": hr_60s,
                "hashrate_15m": hr_15m,
                "hashrate_max": hr_max,
                "shares_good": shares_good,
                "shares_total": shares_total,
                "shares_rejected": shares_rejected,
                "diff": diff,
                "diff_formatted": format_diff(diff),
                "pool": pool,
                "uptime": uptime_str,
                "algo": algo,
                "threads": cpu_threads,
                "hugepages": hp_str,
                "paused": is_paused,
                "raw_error": None
            }
            _LAST_VALID_METRICS = metrics
            return metrics
        else:
            logger.warning(f"XMRig API respondió con código {resp.status_code}: {resp.text}")
            error_msg = f"HTTP {resp.status_code}"
    except Exception as e:
        logger.debug(f"No se pudo contactar a la API de XMRig ({XMRIG_API_URL}): {e}")
        error_msg = str(e)

    # Si la petición falló, verificar si el proceso está detenido por el Watchdog (SIGSTOP)
    proc_state = check_xmrig_process_state()
    if proc_state == "T":
        logger.info("Proceso xmrig detectado en estado 'T' (detenido por SIGSTOP de watchdog).")
        if _LAST_VALID_METRICS:
            m = dict(_LAST_VALID_METRICS)
            m["status"] = "PAUSADO (Watchdog)"
            m["hashrate_10s"] = 0.0
            m["paused"] = True
            m["raw_error"] = "Proceso pausado por control de carga"
            return m
        return {
            "status": "PAUSADO (Watchdog)",
            "hashrate_10s": 0.0,
            "hashrate_60s": 0.0,
            "hashrate_15m": 0.0,
            "hashrate_max": 0.0,
            "shares_good": 0,
            "shares_total": 0,
            "shares_rejected": 0,
            "diff": 0,
            "diff_formatted": "---",
            "pool": "MoneroOcean",
            "uptime": "---",
            "algo": "rx/0",
            "threads": 8,
            "hugepages": "---",
            "paused": True,
            "raw_error": "Proceso pausado por control de carga"
        }

    # Si no es Linux y no hay conexión, fallback a mock para desarrollo
    if sys.platform != "linux":
        return get_mock_miner_metrics()

    # Si no respondió y no está en SIGSTOP -> OFFLINE
    return {
        "status": "OFFLINE",
        "hashrate_10s": 0.0,
        "hashrate_60s": 0.0,
        "hashrate_15m": 0.0,
        "hashrate_max": 0.0,
        "shares_good": 0,
        "shares_total": 0,
        "shares_rejected": 0,
        "diff": 0,
        "diff_formatted": "---",
        "pool": "Desconectado",
        "uptime": "---",
        "algo": "rx/0",
        "threads": 0,
        "hugepages": "---",
        "paused": False,
        "raw_error": error_msg
    }
