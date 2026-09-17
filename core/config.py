# -*- coding: utf-8 -*-
"""
配置管理模块
负责读写用户目录下的 config.json，首次运行自动创建默认配置
"""
import json
import os


class ConfigManager:
    """配置管理器：加载、保存、读取用户配置"""

    def __init__(self):
        # 配置目录：%USERPROFILE%\.newsweatherapp\
        self.config_dir = os.path.join(os.path.expanduser("~"), ".newsweatherapp")
        self.config_file = os.path.join(self.config_dir, "config.json")

        # 默认配置
        self.default_config = {
            "city": "北京",
            "city_id": "101010100",
            "qweather_api_key": "",
            "newsapi_key": "",
            "news_provider": "newsapi",   # newsapi 或 juhe
            "tts_rate": 1.0,               # 语速倍率 0.5~2.0
            "tts_voice": "",               # 音色 ID，空字符串表示默认
            "broadcast_mode": "mixed",    # weather / news / mixed
            "update_interval": 600         # 自动刷新间隔（秒）
        }

        self.config = self.load()

    def load(self):
        """加载配置文件，不存在则创建默认配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                # 与默认配置合并，确保新增字段有值
                merged = self.default_config.copy()
                merged.update(cfg)
                return merged
            except Exception:
                return self.default_config.copy()
        else:
            # 首次运行，自动创建配置文件
            self.save(self.default_config.copy())
            return self.default_config.copy()

    def save(self, config=None):
        """保存配置到文件"""
        if config is None:
            config = self.config
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.config = config

    def get(self, key, default=None):
        """读取某项配置"""
        return self.config.get(key, default)

    def set(self, key, value):
        """设置某项配置并立即保存"""
        self.config[key] = value
        self.save()
