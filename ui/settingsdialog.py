# -*- coding: utf-8 -*-
"""
设置对话框
- 默认城市输入 + 城市搜索
- 语速滑块（0.5x ~ 2.0x）
- 音色下拉选择（从 pyttsx3 获取系统可用音色）
- 播报模式（天气 / 新闻 / 混合）
- API Key 配置（和风天气 + 新闻数据源）
保存到 %USERPROFILE%\.newsweatherapp\config.json
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QSlider, QPushButton, QGroupBox,
    QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from core.weatherapi import WeatherAPI


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config, tts_engine, parent=None):
        super().__init__(parent)
        self.config = config
        self.tts = tts_engine
        self._weather_api = WeatherAPI(config.get("qweather_api_key", ""))

        self._init_ui()
        self._load_values()

    def _init_ui(self):
        self.setWindowTitle("设置")
        self.resize(520, 620)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── API 配置 ──
        api_group = QGroupBox("API 配置")
        api_form = QFormLayout(api_group)

        # 和风天气 API Key
        self.qweather_key_input = QLineEdit()
        self.qweather_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.qweather_key_input.setPlaceholderText("在和风天气开发者平台注册获取")
        api_form.addRow("和风天气 API Key:", self.qweather_key_input)

        # 新闻数据源
        self.news_provider_combo = QComboBox()
        self.news_provider_combo.addItems(["newsapi", "juhe"])
        api_form.addRow("新闻数据源:", self.news_provider_combo)

        # 新闻 API Key
        self.news_key_input = QLineEdit()
        self.news_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.news_key_input.setPlaceholderText("在对应平台注册获取")
        api_form.addRow("新闻 API Key:", self.news_key_input)

        layout.addWidget(api_group)

        # ── 城市设置 ──
        city_group = QGroupBox("城市设置")
        city_layout = QVBoxLayout(city_group)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("默认城市:"))
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("输入城市名，如：北京")
        search_row.addWidget(self.city_input)

        self.city_search_btn = QPushButton("搜索")
        self.city_search_btn.setFixedWidth(70)
        self.city_search_btn.clicked.connect(self._search_city)
        search_row.addWidget(self.city_search_btn)

        city_layout.addLayout(search_row)

        self.city_result_combo = QComboBox()
        self.city_result_combo.setVisible(False)
        city_layout.addWidget(self.city_result_combo)

        layout.addWidget(city_group)

        # ── 语音播报设置 ──
        tts_group = QGroupBox("语音播报设置")
        tts_layout = QVBoxLayout(tts_group)

        # 音色选择
        voice_row = QHBoxLayout()
        voice_row.addWidget(QLabel("音色选择:"))
        self.voice_combo = QComboBox()
        self.voice_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        voices = self.tts.get_voices()
        for v in voices:
            name = v.name if hasattr(v, "name") else str(v)
            vid = v.id if hasattr(v, "id") else name
            self.voice_combo.addItem(name, vid)
        voice_row.addWidget(self.voice_combo)
        tts_layout.addLayout(voice_row)

        # 语速滑块
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("语速:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 200)  # 0.5x ~ 2.0x
        self.speed_slider.setValue(100)
        self.speed_label = QLabel("1.0x")
        self.speed_label.setFixedWidth(40)
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v / 100:.1f}x")
        )
        speed_row.addWidget(self.speed_slider)
        speed_row.addWidget(self.speed_label)
        tts_layout.addLayout(speed_row)

        # 播报模式
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("播报模式:"))
        self.broadcast_combo = QComboBox()
        self.broadcast_combo.addItems(["天气播报", "新闻播报", "混合播报"])
        self.broadcast_combo.setCurrentIndex(2)
        mode_row.addWidget(self.broadcast_combo)
        tts_layout.addLayout(mode_row)

        layout.addWidget(tts_group)

        # ── 按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("保存")
        save_btn.setObjectName("saveBtn")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _load_values(self):
        """从配置加载当前值"""
        self.qweather_key_input.setText(self.config.get("qweather_api_key", ""))
        self.news_key_input.setText(self.config.get("newsapi_key", ""))
        self.news_provider_combo.setCurrentText(self.config.get("news_provider", "newsapi"))
        self.city_input.setText(self.config.get("city", "北京"))

        rate = self.config.get("tts_rate", 1.0)
        self.speed_slider.setValue(int(rate * 100))

        voice_id = self.config.get("tts_voice", "")
        if voice_id:
            idx = self.voice_combo.findData(voice_id)
            if idx >= 0:
                self.voice_combo.setCurrentIndex(idx)

        mode = self.config.get("broadcast_mode", "mixed")
        mode_map = {"weather": 0, "news": 1, "mixed": 2}
        self.broadcast_combo.setCurrentIndex(mode_map.get(mode, 2))

    def _search_city(self):
        """搜索城市"""
        city_name = self.city_input.text().strip()
        if not city_name:
            return

        if not self.config.get("qweather_api_key"):
            QMessageBox.warning(self, "提示", "请先配置和风天气 API Key")
            return

        results = self._weather_api.search_city(city_name)
        if results:
            self.city_result_combo.clear()
            for loc in results:
                name = f"{loc.get('name', '')} - {loc.get('adm1', '')} {loc.get('adm2', '')}"
                self.city_result_combo.addItem(name, loc.get("id", ""))
            self.city_result_combo.setVisible(True)
        else:
            QMessageBox.information(self, "提示", "未找到匹配的城市，请检查城市名或 API Key")

    def _save(self):
        """保存设置"""
        self.config.set("qweather_api_key", self.qweather_key_input.text().strip())
        self.config.set("newsapi_key", self.news_key_input.text().strip())
        self.config.set("news_provider", self.news_provider_combo.currentText())
        self.config.set("city", self.city_input.text().strip())

        # 城市搜索结果
        if self.city_result_combo.count() > 0 and self.city_result_combo.isVisible():
            city_id = self.city_result_combo.currentData()
            if city_id:
                self.config.set("city_id", city_id)

        self.config.set("tts_rate", self.speed_slider.value() / 100.0)
        self.config.set("tts_voice", self.voice_combo.currentData())

        mode_map = {0: "weather", 1: "news", 2: "mixed"}
        self.config.set("broadcast_mode", mode_map.get(self.broadcast_combo.currentIndex(), "mixed"))

        self.config.save()
        self.accept()
