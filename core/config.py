# -*- coding: utf-8 -*-
"""
配置管理模块
支持环境变量自动配置（CI/CD 场景）
"""
import json
import os


class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".newsweatherapp")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.default_config = {
            "city": "北京",
            "city_id": "101010100",
            "qweather_api_key": "",
            "newsapi_key": "",
            "news_provider": "newsapi",
            "tts_rate": 1.0,
            "tts_voice": "",
            "broadcast_mode": "mixed",
            "update_interval": 600
        }
        self.config = self.load()

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                merged = self.default_config.copy()
                merged.update(cfg)
                env_qw = os.environ.get("QWEATHER_API_KEY", "")
                if env_qw and not merged.get("qweather_api_key"):
                    merged["qweather_api_key"] = env_qw
                env_na = os.environ.get("NEWSAPI_KEY", "")
                if env_na and not merged.get("newsapi_key"):
                    merged["newsapi_key"] = env_na
                env_city = os.environ.get("DEFAULT_CITY", "")
                if env_city:
                    merged["city"] = env_city
                return merged
            except Exception:
                return self.default_config.copy()
        else:
            cfg = self.default_config.copy()
            env_qw = os.environ.get("QWEATHER_API_KEY", "")
            if env_qw:
                cfg["qweather_api_key"] = env_qw
            env_na = os.environ.get("NEWSAPI_KEY", "")
            if env_na:
                cfg["newsapi_key"] = env_na
            env_city = os.environ.get("DEFAULT_CITY", "")
            if env_city:
                cfg["city"] = env_city
            self.save(cfg)
            return cfg

    def save(self, config=None):
        if config is None:
            config = self.config
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.config = config

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()
