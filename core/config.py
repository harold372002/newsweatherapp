# -*- coding: utf-8 -*-
"""
配置管理模块 — 无需 API Key 版本
"""
import json
import os


class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".newsweatherapp")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.default_config = {
            "city": "北京",
            "city_id": "39.9042,116.4074",
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
                return merged
            except Exception:
                return self.default_config.copy()
        else:
            self.save(self.default_config.copy())
            return self.default_config.copy()

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
