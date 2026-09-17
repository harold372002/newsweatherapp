# -*- coding: utf-8 -*-
"""
主窗口（Dashboard）
布局：
  顶部：天气卡片 + 播报按钮 + 设置按钮
  中部：头条轮播
  底部：新闻分类 Tab + 新闻列表
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStatusBar, QMenuBar, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

from core.config import ConfigManager
from core.weatherapi import WeatherAPI
from core.newsapi import NewsAPI
from core.ttsengine import TTSEngine
from core import Worker

from ui.weatherwidget import WeatherCardWidget, WeatherDetailDialog
from ui.newswidget import HeadlineCarousel, NewsTabWidget
from ui.detaildialog import NewsDetailDialog
from ui.settingsdialog import SettingsDialog


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.weather_api = WeatherAPI(config.get("qweather_api_key", ""))
        self.news_api = NewsAPI(
            config.get("newsapi_key", ""),
            config.get("news_provider", "newsapi")
        )
        self.tts = TTSEngine()
        self.tts.set_rate(config.get("tts_rate", 1.0))
        self.tts.set_voice(config.get("tts_voice", ""))

        self.weather_data = {}
        self.news_data = {}
        self.headlines = []
        self._broadcasting = False
        self._broadcast_queue = []
        self._current_broadcast_id = ""

        # 保持 Worker 引用，防止被 GC
        self._workers = []

        # 自动刷新定时器
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._load_data)
        interval = config.get("update_interval", 600) * 1000
        self._refresh_timer.start(interval)

        self._init_ui()
        self._init_signals()
        self._load_data()

    # ────────────── UI 初始化 ──────────────

    def _init_ui(self):
        self.setWindowTitle("新闻天气播报")
        self.resize(960, 720)
        self.setMinimumSize(800, 600)

        # 中央控件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # ── 顶部栏：天气卡片 + 按钮 ──
        top_bar = QHBoxLayout()
        self.weather_card = WeatherCardWidget()
        top_bar.addWidget(self.weather_card, 1)

        # 按钮容器
        btn_col = QVBoxLayout()
        btn_col.setSpacing(6)

        self.broadcast_btn = QPushButton("🔊 播报")
        self.broadcast_btn.setObjectName("broadcastBtn")
        self.broadcast_btn.setFixedSize(110, 42)
        self.broadcast_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_col.addWidget(self.broadcast_btn)

        self.settings_btn = QPushButton("⚙ 设置")
        self.settings_btn.setFixedSize(110, 36)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_col.addWidget(self.settings_btn)

        btn_col.addStretch()
        top_bar.addLayout(btn_col)
        layout.addLayout(top_bar)

        # ── 头条轮播 ──
        self.carousel = HeadlineCarousel()
        layout.addWidget(self.carousel)

        # ── 新闻列表 ──
        self.news_widget = NewsTabWidget()
        layout.addWidget(self.news_widget, 1)

        # ── 状态栏 ──
        self.statusBar().showMessage("就绪")

        # ── 菜单栏 ──
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        refresh_action = QAction("刷新数据", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._load_data)
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("设置")
        open_settings_action = QAction("打开设置", self)
        open_settings_action.triggered.connect(self._open_settings)
        settings_menu.addAction(open_settings_action)

        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_signals(self):
        """连接信号"""
        self.broadcast_btn.clicked.connect(self._on_broadcast)
        self.settings_btn.clicked.connect(self._open_settings)
        self.weather_card.clicked.connect(self._open_weather_detail)
        self.carousel.clicked.connect(self._open_news_detail)
        self.news_widget.news_clicked.connect(self._open_news_detail)

        self.tts.speak_started.connect(self._on_tts_started)
        self.tts.speak_finished.connect(self._on_tts_finished)

    # ────────────── 数据加载 ──────────────

    def _load_data(self):
        """加载天气和新闻数据"""
        self._load_weather()
        self._load_news()

    def _load_weather(self):
        """加载天气数据"""
        city_id = self.config.get("city_id", "101010100")

        if not self.config.get("qweather_api_key"):
            self.weather_card.show_message("请先在设置中配置和风天气 API Key")
            return

        self.statusBar().showMessage("正在加载天气数据...")
        worker = Worker(self._fetch_weather, city_id)
        worker.result_ready.connect(self._on_weather_loaded)
        worker.error_occurred.connect(
            lambda e: self.statusBar().showMessage(f"天气数据加载失败: {e}")
        )
        worker.start()
        self._workers.append(worker)

    def _fetch_weather(self, city_id):
        """在后台线程中获取天气数据"""
        now = self.weather_api.get_current_weather(city_id)
        daily = self.weather_api.get_7day_forecast(city_id)
        hourly = self.weather_api.get_24h_forecast(city_id)
        aqi = self.weather_api.get_air_quality(city_id)
        return {"now": now, "daily": daily, "hourly": hourly, "aqi": aqi}

    def _on_weather_loaded(self, data):
        """天气数据加载完成"""
        self.weather_data = data
        city = self.config.get("city", "北京")
        self.weather_card.update_weather(data, city)
        self.statusBar().showMessage("天气数据已更新", 3000)

    def _load_news(self):
        """加载新闻数据"""
        if not self.config.get("newsapi_key"):
            self.news_widget.show_message("请先在设置中配置新闻 API Key")
            return

        self.statusBar().showMessage("正在加载新闻数据...")
        worker = Worker(self._fetch_all_news)
        worker.result_ready.connect(self._on_news_loaded)
        worker.error_occurred.connect(
            lambda e: self.statusBar().showMessage(f"新闻数据加载失败: {e}")
        )
        worker.start()
        self._workers.append(worker)

    def _fetch_all_news(self):
        """在后台线程中获取所有分类新闻"""
        categories = ["top", "technology", "sports", "business", "entertainment"]
        result = {}
        for cat in categories:
            result[cat] = self.news_api.get_headlines(cat)
        return result

    def _on_news_loaded(self, data):
        """新闻数据加载完成"""
        self.news_data = data
        self.news_widget.update_news(data)
        # 更新头条轮播
        self.headlines = data.get("top", [])[:10]
        self.carousel.set_headlines(self.headlines)
        self.statusBar().showMessage("新闻数据已更新", 3000)

    # ────────────── 语音播报 ──────────────

    def _on_broadcast(self):
        """播报按钮点击"""
        if self._broadcasting:
            self._stop_broadcast()
        else:
            self._start_broadcast()

    def _start_broadcast(self):
        """开始播报"""
        mode = self.config.get("broadcast_mode", "mixed")
        self._broadcast_queue = []

        if mode in ("weather", "mixed"):
            weather_text = self._generate_weather_text()
            if weather_text:
                self._broadcast_queue.append(("weather", weather_text))

        if mode in ("news", "mixed"):
            top_news = self.news_data.get("top", [])[:5]
            for i, news in enumerate(top_news):
                title = news.get("title", "")
                text = f"第{i + 1}条新闻，{title}。"
                self._broadcast_queue.append((f"news_{i}", text))

        if not self._broadcast_queue:
            self.statusBar().showMessage("没有可播报的内容", 3000)
            return

        self._broadcasting = True
        self.broadcast_btn.setText("⏹ 停止")
        self._speak_next_broadcast()

    def _speak_next_broadcast(self):
        """播报队列中的下一条"""
        if not self._broadcast_queue:
            self._stop_broadcast()
            return

        text_id, text = self._broadcast_queue.pop(0)
        self._current_broadcast_id = text_id

        # 高亮当前条目
        if text_id.startswith("news_"):
            idx = int(text_id.split("_")[1])
            self.carousel.set_highlight(idx)
            self.news_widget.highlight_item("top", idx)
        else:
            self.carousel.set_highlight(-1)

        self.tts.speak(text, text_id)

    def _stop_broadcast(self):
        """停止播报"""
        self._broadcasting = False
        self._broadcast_queue = []
        self._current_broadcast_id = ""
        self.tts.stop()
        self.broadcast_btn.setText("🔊 播报")
        self.carousel.set_highlight(-1)
        self.statusBar().showMessage("播报已停止", 3000)

    def _generate_weather_text(self):
        """生成自然口语化的天气播报文案"""
        now = self.weather_data.get("now", {})
        daily = self.weather_data.get("daily", [])
        aqi = self.weather_data.get("aqi", {})

        if not now:
            return ""

        city = self.config.get("city", "北京")
        text = now.get("text", "")
        temp = now.get("temp", "")
        feels_like = now.get("feelsLike", "")
        humidity = now.get("humidity", "")
        wind_dir = now.get("windDir", "")
        wind_scale = now.get("windScale", "")
        aq_category = aqi.get("category", "")

        # 今日温度范围
        if daily:
            temp_max = daily[0].get("tempMax", "")
            temp_min = daily[0].get("tempMin", "")
        else:
            temp_max = temp
            temp_min = temp

        parts = [f"{city}今天{text}"]

        if temp_min and temp_max and temp_min != temp_max:
            parts.append(f"气温{temp_min}到{temp_max}度")
        elif temp:
            parts.append(f"气温{temp}度")

        if feels_like:
            parts.append(f"体感温度{feels_like}度")

        if aq_category:
            parts.append(f"空气质量{aq_category}")

        if wind_dir and wind_scale:
            parts.append(f"{wind_dir}风{wind_scale}级")

        if humidity:
            parts.append(f"湿度百分之{humidity}")

        # 出行建议
        if text:
            if "晴" in text and aq_category and ("优" in aq_category or "良" in aq_category):
                parts.append("适合外出活动")
            elif "雨" in text:
                parts.append("出门记得带伞")
            elif "雪" in text:
                parts.append("注意保暖防滑")
            elif "霾" in text or "雾" in text:
                parts.append("外出建议佩戴口罩")

        return "，".join(parts) + "。"

    def _on_tts_started(self, text_id):
        """TTS 开始播报"""
        self.statusBar().showMessage("正在播报...")

    def _on_tts_finished(self, text_id):
        """TTS 播报结束"""
        if self._broadcasting and text_id == self._current_broadcast_id:
            self._speak_next_broadcast()
        elif not self._broadcasting:
            self.statusBar().showMessage("播报结束", 3000)

    # ────────────── 弹窗 ──────────────

    def _open_weather_detail(self):
        """打开天气详情"""
        if not self.weather_data or not self.weather_data.get("now"):
            QMessageBox.information(self, "提示", "暂无天气数据，请先配置 API Key 并刷新")
            return
        dialog = WeatherDetailDialog(
            self.weather_data,
            self.config.get("city", "北京"),
            self
        )
        dialog.exec()

    def _open_news_detail(self, news_item):
        """打开新闻详情"""
        dialog = NewsDetailDialog(news_item, self.news_api, self.tts, self)
        dialog.exec()

    def _open_settings(self):
        """打开设置"""
        dialog = SettingsDialog(self.config, self.tts, self)
        if dialog.exec():
            # 设置已保存，更新 API 和 TTS 参数
            self.weather_api.api_key = self.config.get("qweather_api_key", "")
            self.news_api.api_key = self.config.get("newsapi_key", "")
            self.news_api.provider = self.config.get("news_provider", "newsapi")
            self.tts.set_rate(self.config.get("tts_rate", 1.0))
            self.tts.set_voice(self.config.get("tts_voice", ""))

            # 更新刷新间隔
            self._refresh_timer.setInterval(
                self.config.get("update_interval", 600) * 1000
            )

            # 重新加载数据
            self._load_data()

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "<h3>新闻天气播报</h3>"
            "<p>版本 1.0.0</p>"
            "<p>一个集新闻播报与天气查询于一体的桌面应用。</p>"
            "<p>技术栈：Python 3.11 + PyQt6 + pyttsx3</p>"
        )

    # ────────────── 清理 ──────────────

    def closeEvent(self, event):
        """窗口关闭时清理资源"""
        self.tts.shutdown()
        super().closeEvent(event)
