# -*- coding: utf-8 -*-
"""
和风天气 API 封装
文档：https://dev.qweather.com/
免费版每天 1000 次调用
"""
import requests


class WeatherAPI:
    """和风天气 API 封装类"""

    BASE_URL = "https://devapi.qweather.com/v7"
    GEO_URL = "https://geoapi.qweather.com/v2/city/lookup"

    def __init__(self, api_key):
        self.api_key = api_key

    def _is_ready(self):
        """检查 API Key 是否已配置"""
        return bool(self.api_key)

    def search_city(self, city_name):
        """
        城市搜索：根据城市名获取城市 ID
        返回 location 列表，每项含 id / name / adm1 / adm2 / lat / lon
        """
        if not self._is_ready():
            return []
        params = {"location": city_name, "key": self.api_key}
        try:
            resp = requests.get(self.GEO_URL, params=params, timeout=10)
            data = resp.json()
            if data.get("code") == "200":
                return data.get("location", [])
            return []
        except Exception:
            return []

    def get_current_weather(self, location_id):
        """
        获取实时天气
        返回 now 字典，含 temp / feelsLike / text / humidity / windDir / windScale / windSpeed / obsTime 等
        """
        if not self._is_ready():
            return {}
        params = {"location": location_id, "key": self.api_key}
        try:
            resp = requests.get(f"{self.BASE_URL}/weather/now", params=params, timeout=10)
            data = resp.json()
            if data.get("code") == "200":
                return data.get("now", {})
            return {}
        except Exception:
            return {}

    def get_7day_forecast(self, location_id):
        """
        获取 7 天天气预报
        返回 daily 列表，每项含 fxDate / tempMax / tempMin / textDay / textNight / windDirDay 等
        """
        if not self._is_ready():
            return []
        params = {"location": location_id, "key": self.api_key}
        try:
            resp = requests.get(f"{self.BASE_URL}/weather/7d", params=params, timeout=10)
            data = resp.json()
            if data.get("code") == "200":
                return data.get("daily", [])
            return []
        except Exception:
            return []

    def get_24h_forecast(self, location_id):
        """
        获取 24 小时天气预报
        返回 hourly 列表，每项含 fxTime / temp / text / humidity / windDir / windScale 等
        """
        if not self._is_ready():
            return []
        params = {"location": location_id, "key": self.api_key}
        try:
            resp = requests.get(f"{self.BASE_URL}/weather/24h", params=params, timeout=10)
            data = resp.json()
            if data.get("code") == "200":
                return data.get("hourly", [])
            return []
        except Exception:
            return []

    def get_air_quality(self, location_id):
        """
        获取实时空气质量
        返回 now 字典，含 aqi / category / pm2p5 / pm10 / primary 等
        """
        if not self._is_ready():
            return {}
        url = "https://devapi.qweather.com/v7/air/now"
        params = {"location": location_id, "key": self.api_key}
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("code") == "200":
                return data.get("now", {})
            return {}
        except Exception:
            return {}
