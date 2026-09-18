# -*- coding: utf-8 -*-
"""
和风天气 API 封装 — 改用 Open-Meteo 免费天气 API
无需 API Key，每天无限次调用
文档：https://open-meteo.com/
"""
import requests


class WeatherAPI:
    """Open-Meteo 免费天气 API 封装类（无需 API Key）"""

    GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

    WMO_CODES = {
        0: "晴", 1: "晴间多云", 2: "多云", 3: "阴",
        45: "有雾", 48: "雾凇",
        51: "毛毛雨", 53: "毛毛雨", 55: "毛毛雨",
        56: "冻毛毛雨", 57: "冻毛毛雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        66: "冻雨", 67: "冻雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        77: "雪粒",
        80: "小阵雨", 81: "阵雨", 82: "暴雨",
        85: "小阵雪", 86: "大阵雪",
        95: "雷暴", 96: "雷暴伴冰雹", 99: "严重雷暴",
    }

    def __init__(self, api_key=""):
        pass

    def _is_ready(self):
        return True

    def search_city(self, city_name):
        params = {"name": city_name, "count": 10, "language": "zh", "format": "json"}
        try:
            resp = requests.get(self.GEO_URL, params=params, timeout=10)
            data = resp.json()
            results = []
            for loc in data.get("results", []):
                lat = loc.get("latitude", 0)
                lon = loc.get("longitude", 0)
                results.append({
                    "id": f"{lat},{lon}",
                    "name": loc.get("name", ""),
                    "adm1": loc.get("admin1", ""),
                    "adm2": loc.get("country", ""),
                    "lat": lat,
                    "lon": lon,
                })
            return results
        except Exception:
            return []

    def get_current_weather(self, location_id):
        lat, lon = self._parse_location(location_id)
        params = {
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                       "weather_code,wind_speed_10m,wind_direction_10m",
            "timezone": "Asia/Shanghai",
        }
        try:
            resp = requests.get(self.WEATHER_URL, params=params, timeout=10)
            data = resp.json()
            cur = data.get("current", {})
            wcode = cur.get("weather_code", 0)
            return {
                "temp": str(int(round(cur.get("temperature_2m", 0)))),
                "feelsLike": str(int(round(cur.get("apparent_temperature", 0)))),
                "text": self.WMO_CODES.get(wcode, "未知"),
                "humidity": str(int(cur.get("relative_humidity_2m", 0))),
                "windDir": self._wind_dir(cur.get("wind_direction_10m", 0)),
                "windScale": self._wind_scale(cur.get("wind_speed_10m", 0)),
                "windSpeed": str(int(cur.get("wind_speed_10m", 0))),
                "obsTime": cur.get("time", ""),
            }
        except Exception:
            return {}

    def get_7day_forecast(self, location_id):
        lat, lon = self._parse_location(location_id)
        params = {
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,weather_code,"
                     "wind_direction_10m_dominant,wind_speed_10m_max",
            "timezone": "Asia/Shanghai",
            "forecast_days": 7,
        }
        try:
            resp = requests.get(self.WEATHER_URL, params=params, timeout=10)
            data = resp.json()
            daily = data.get("daily", {})
            result = []
            times = daily.get("time", [])
            tmax = daily.get("temperature_2m_max", [])
            tmin = daily.get("temperature_2m_min", [])
            wcodes = daily.get("weather_code", [])
            for i in range(len(times)):
                result.append({
                    "fxDate": times[i],
                    "tempMax": str(int(round(tmax[i]))) if i < len(tmax) else "--",
                    "tempMin": str(int(round(tmin[i]))) if i < len(tmin) else "--",
                    "textDay": self.WMO_CODES.get(wcodes[i], "未知") if i < len(wcodes) else "--",
                    "textNight": self.WMO_CODES.get(wcodes[i], "未知") if i < len(wcodes) else "--",
                })
            return result
        except Exception:
            return []

    def get_24h_forecast(self, location_id):
        lat, lon = self._parse_location(location_id)
        params = {
            "latitude": lat, "longitude": lon,
            "hourly": "temperature_2m,weather_code",
            "timezone": "Asia/Shanghai",
            "forecast_hours": 24,
        }
        try:
            resp = requests.get(self.WEATHER_URL, params=params, timeout=10)
            data = resp.json()
            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            temps = hourly.get("temperature_2m", [])
            wcodes = hourly.get("weather_code", [])
            result = []
            for i in range(len(times)):
                result.append({
                    "fxTime": times[i],
                    "temp": str(int(round(temps[i]))) if i < len(temps) else "0",
                    "text": self.WMO_CODES.get(wcodes[i], "未知") if i < len(wcodes) else "--",
                })
            return result
        except Exception:
            return []

    def get_air_quality(self, location_id):
        lat, lon = self._parse_location(location_id)
        params = {
            "latitude": lat, "longitude": lon,
            "current": "pm2_5,pm10,european_aqi",
            "timezone": "Asia/Shanghai",
        }
        try:
            resp = requests.get(self.AIR_URL, params=params, timeout=10)
            data = resp.json()
            cur = data.get("current", {})
            aqi = cur.get("european_aqi", 0)
            return {
                "aqi": str(int(aqi)),
                "category": self._aqi_category(aqi),
                "pm2p5": str(cur.get("pm2_5", 0)),
                "pm10": str(cur.get("pm10", 0)),
            }
        except Exception:
            return {}

    def _parse_location(self, location_id):
        try:
            parts = str(location_id).split(",")
            return float(parts[0]), float(parts[1])
        except Exception:
            return 39.9042, 116.4074

    def _wind_dir(self, degrees):
        dirs = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]
        idx = int((degrees + 22.5) / 45) % 8
        return dirs[idx]

    def _wind_scale(self, speed_kmh):
        scales = [(1, 0), (6, 1), (12, 2), (20, 3), (29, 4), (39, 5),
                  (50, 6), (62, 7), (75, 8), (89, 9), (103, 10), (118, 11)]
        for threshold, level in scales:
            if speed_kmh < threshold:
                return str(level)
        return "12"

    def _aqi_category(self, aqi):
        if aqi <= 20:
            return "优"
        elif aqi <= 40:
            return "良"
        elif aqi <= 60:
            return "轻度污染"
        elif aqi <= 80:
            return "中度污染"
        elif aqi <= 100:
            return "重度污染"
        else:
            return "严重污染"
