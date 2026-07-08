import os
import sys
import time
import socket
import logging

logger = logging.getLogger(__name__)

def _get_linux_cpu_times():
    try:
        with open("/proc/stat", "r") as f:
            line = f.readline()
        fields = line.strip().split()
        if len(fields) >= 5:
            # cpu user nice system idle iowait irq softirq steal
            times = [float(x) for x in fields[1:9]]
            idle = times[3] + times[4]  # idle + iowait
            total = sum(times)
            return idle, total
    except Exception as e:
        logger.error(f"Error reading CPU times from /proc/stat: {e}")
    return 0, 0

def get_cpu_usage():
    if sys.platform != "linux":
        # Mock values for macOS/local testing
        import random
        return round(random.uniform(5.0, 20.0), 1)

    try:
        idle1, total1 = _get_linux_cpu_times()
        time.sleep(0.1)
        idle2, total2 = _get_linux_cpu_times()
        
        idle_diff = idle2 - idle1
        total_diff = total2 - total1
        
        if total_diff == 0:
            return 0.0
        
        cpu_percentage = 100.0 * (1.0 - (idle_diff / total_diff))
        return round(cpu_percentage, 1)
    except Exception as e:
        logger.error(f"Error calculating CPU usage: {e}")
        return 0.0

def get_cpu_temp():
    if sys.platform != "linux":
        # Mock temperature for macOS
        import random
        return round(random.uniform(35.0, 50.0), 1)

    # Search for common thermal zone paths
    temp_paths = [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/thermal/thermal_zone1/temp",
        "/sys/devices/virtual/thermal/thermal_zone0/temp"
    ]
    for path in temp_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    temp_raw = f.read().strip()
                return round(float(temp_raw) / 1000.0, 1)
            except Exception as e:
                logger.debug(f"Could not read temperature from {path}: {e}")
    
    return 0.0

def get_ram_usage():
    if sys.platform != "linux":
        # Mock RAM usage percentage
        return 45.2

    try:
        mem_info = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    name = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    mem_info[name] = float(val)
        
        total = mem_info.get("MemTotal", 0)
        available = mem_info.get("MemAvailable", mem_info.get("MemFree", 0))
        
        if total == 0:
            return 0.0
        
        used = total - available
        ram_percentage = (used / total) * 100.0
        return round(ram_percentage, 1)
    except Exception as e:
        logger.error(f"Error reading RAM usage: {e}")
        return 0.0

def get_disk_usage():
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        used = total - free
        if total == 0:
            return 0.0
        disk_percentage = (used / total) * 100.0
        return round(disk_percentage, 1)
    except Exception as e:
        logger.error(f"Error reading disk usage: {e}")
        return 0.0

def get_ip_address():
    try:
        # Standard trick to find local IP mapping
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to listing interfaces
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def get_uptime():
    if sys.platform != "linux":
        return "1d 4h 12m"

    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
        
        days = int(uptime_seconds // (24 * 3600))
        hours = int((uptime_seconds % (24 * 3600)) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        
        return " ".join(parts)
    except Exception as e:
        logger.error(f"Error reading uptime: {e}")
        return "unknown"

def get_all_metrics():
    return {
        "cpu": get_cpu_usage(),
        "temp": get_cpu_temp(),
        "ram": get_ram_usage(),
        "disk": get_disk_usage(),
        "ip": get_ip_address(),
        "uptime": get_uptime()
    }

if __name__ == "__main__":
    # Self-test when executed directly
    print("Métricas del Sistema:")
    for k, v in get_all_metrics().items():
        print(f"  {k:8s}: {v}")
