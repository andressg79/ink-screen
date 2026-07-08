import os
import requests
import logging

logger = logging.getLogger(__name__)

# Default coordinates: Montevideo, Uruguay (Latitude: -34.9011, Longitude: -56.1645)
DEFAULT_LAT = -34.9011
DEFAULT_LON = -56.1645

# Map WMO weather codes to text and simple icons
WMO_CODES = {
    0: ("Despejado", "☀️"),
    1: ("Principalmente Despejado", "☀️"),
    2: ("Parcialmente Nublado", "⛅"),
    3: ("Nublado", "☁️"),
    45: ("Niebla", "🌫️"),
    48: ("Niebla Escarcha", "🌫️"),
    51: ("Llovizna Ligera", "🌧️"),
    53: ("Llovizna Moderada", "🌧️"),
    55: ("Llovizna Densa", "🌧️"),
    56: ("Llovizna Helada Ligera", "🌧️"),
    57: ("Llovizna Helada Densa", "🌧️"),
    61: ("Lluvia Ligera", "🌧️"),
    63: ("Lluvia Moderada", "🌧️"),
    65: ("Lluvia Fuerte", "🌧️"),
    66: ("Lluvia Helada Ligera", "🌧️"),
    67: ("Lluvia Helada Densa", "🌧️"),
    71: ("Nevada Ligera", "❄️"),
    73: ("Nevada Moderada", "❄️"),
    75: ("Nevada Fuerte", "❄️"),
    77: ("Granizo de Nieve", "❄️"),
    80: ("Chubascos Lluvia Ligeros", "🌧️"),
    81: ("Chubascos Lluvia Moderados", "🌧️"),
    82: ("Chubascos Lluvia Violentos", "⛈️"),
    85: ("Chubascos Nieve Ligeros", "❄️"),
    86: ("Chubascos Nieve Fuertes", "❄️"),
    95: ("Tormenta Eléctrica", "⚡"),
    96: ("Tormenta con Granizo Ligero", "⛈️"),
    99: ("Tormenta con Granizo Fuerte", "⛈️")
}

class WeatherService:
    def __init__(self):
        self.lat = float(os.environ.get("WEATHER_LAT", DEFAULT_LAT))
        self.lon = float(os.environ.get("WEATHER_LON", DEFAULT_LON))
        self.cached_weather = {
            "temp": "--.-",
            "condition": "Cargando...",
            "icon": "⏳",
            "humidity": "--",
            "wind": "--.-"
        }

    def fetch_weather(self):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": "auto"
        }
        
        try:
            logger.info(f"Querying weather for Lat={self.lat}, Lon={self.lon}...")
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                current = data.get("current", {})
                
                temp = current.get("temperature_2m", 0.0)
                code = current.get("weather_code", 0)
                humidity = current.get("relative_humidity_2m", 0)
                wind = current.get("wind_speed_10m", 0.0)
                
                condition, icon = WMO_CODES.get(code, ("Desconocido", "❓"))
                
                self.cached_weather = {
                    "temp": f"{temp:.1f}",
                    "condition": condition,
                    "icon": icon,
                    "humidity": f"{humidity}%",
                    "wind": f"{wind:.1f} km/h"
                }
                logger.info(f"Weather fetched: {temp}°C, {condition}")
            else:
                logger.error(f"Weather API returned status code {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to fetch weather: {e}")
            
        return self.cached_weather

    def get_weather(self):
        return self.cached_weather

if __name__ == "__main__":
    # Test execution
    print("Obteniendo clima de prueba...")
    service = WeatherService()
    print("Resultado:", service.fetch_weather())
