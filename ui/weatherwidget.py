# -*- coding: utf-8 -*-
"""
天气卡片 + 天气详情对话框
- WeatherCardWidget：主窗口顶部的紧凑天气卡片，点击可打开详情
- WeatherDetailDialog：天气详情弹窗（大卡片 + 24h 温度趋势图 + 7 天预报）
"""
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QDialog, QGroupBox, QPushButton, QScrollArea,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 配置 matplotlib 暗色主题
plt.rcParams.update({
    "axes.facecolor": "#1e1e2e",
    "figure.facecolor": "#1e1e2e",
    "axes.labelcolor": "#cdd6f4",
    "xtick.color": "#cdd6f4",
    "ytick.color": "#cdd6f4",
    "axes.edgecolor": "#45475a",
    "font.size": 9,
})


class WeatherCardWidget(QFrame):
    """紧凑天气卡片，用于主窗口顶部"""

    clicked = pyqtSignal()  # 点击信号

    def __init__(self):
        super().__init__()
        self.setObjectName("weatherCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)

        # ── 左侧：城市 + 温度 ──
        left = QVBoxLayout()
        self.city_label = QLabel("北京")
        self.city_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa;")

        self.temp_label = QLabel("--°")
        self.temp_label.setStyleSheet("font-size: 42px; font-weight: bold; color: #89b4fa;")

        self.condition_label = QLabel("--")
        self.condition_label.setStyleSheet("font-size: 14px; color: #a6adc8;")

        left.addWidget(self.city_label)
        left.addWidget(self.temp_label)
        left.addWidget(self.condition_label)
        layout.addLayout(left)
        layout.addStretch()

        # ── 右侧：详细数据 ──
        right = QGridLayout()
        right.setSpacing(8)

        self.feels_like_label = QLabel("体感: --")
        self.humidity_label = QLabel("湿度: --")
        self.wind_label = QLabel("风力: --")
        self.aqi_label = QLabel("空气: --")
        self.update_time_label = QLabel("更新: --")

        detail_labels = [
            (self.feels_like_label, 0, 0),
            (self.humidity_label, 0, 1),
            (self.wind_label, 1, 0),
            (self.aqi_label, 1, 1),
            (self.update_time_label, 2, 0, 1, 2),
        ]
        for item in detail_labels:
            label = item[0]
            row, col = item[1], item[2]
            label.setStyleSheet("font-size: 13px; color: #a6adc8;")
            if len(item) == 4:
                right.addWidget(label, row, col, 1, 2)
            else:
                right.addWidget(label, row, col)

        layout.addLayout(right)

    def update_weather(self, data, city_name):
        """更新天气数据"""
        now = data.get("now", {})
        aqi = data.get("aqi", {})

        self.city_label.setText(city_name)
        self.temp_label.setText(f"{now.get('temp', '--')}°")
        self.condition_label.setText(now.get("text", "--"))
        self.feels_like_label.setText(f"体感: {now.get('feelsLike', '--')}°")
        self.humidity_label.setText(f"湿度: {now.get('humidity', '--')}%")
        self.wind_label.setText(f"风力: {now.get('windDir', '--')} {now.get('windScale', '--')}级")
        self.aqi_label.setText(f"空气: {aqi.get('category', '--')}")

        obs_time = now.get("obsTime", "")
        if obs_time:
            time_str = obs_time[:16].replace("T", " ")
            self.update_time_label.setText(f"更新: {time_str}")
        else:
            self.update_time_label.setText("更新: --")

    def show_message(self, msg):
        """显示提示信息（未配置 API Key 时）"""
        self.temp_label.setText("--°")
        self.condition_label.setText(msg)
        self.feels_like_label.setText("体感: --")
        self.humidity_label.setText("湿度: --")
        self.wind_label.setText("风力: --")
        self.aqi_label.setText("空气: --")
        self.update_time_label.setText("更新: --")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class WeatherDetailDialog(QDialog):
    """天气详情对话框：大卡片 + 24h 温度趋势图 + 7 天预报"""

    def __init__(self, weather_data, city_name, parent=None):
        super().__init__(parent)
        self.weather_data = weather_data
        self.city_name = city_name
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("天气详情")
        self.resize(850, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── 大天气卡片 ──
        card = WeatherCardWidget()
        card.update_weather(self.weather_data, self.city_name)
        layout.addWidget(card)

        # ── 24 小时温度趋势图 ──
        chart_group = QGroupBox("24 小时温度趋势")
        chart_layout = QVBoxLayout(chart_group)
        self.chart_canvas = self._create_chart()
        chart_layout.addWidget(self.chart_canvas)
        layout.addWidget(chart_group)

        # ── 7 天预报 ──
        forecast_group = QGroupBox("7 天预报")
        forecast_layout = QVBoxLayout(forecast_group)
        forecast_layout.setSpacing(6)

        daily = self.weather_data.get("daily", [])
        if daily:
            for day in daily:
                item = self._create_forecast_item(day)
                forecast_layout.addWidget(item)
        else:
            forecast_layout.addWidget(QLabel("暂无预报数据"))

        # 添加弹性空间
        forecast_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(forecast_group)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(scroll, 1)

        # ── 关闭按钮 ──
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _create_chart(self):
        """创建 24 小时温度趋势图"""
        fig = Figure(figsize=(8, 3), facecolor="#1e1e2e")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1e1e2e")
        ax.tick_params(colors="#cdd6f4", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#45475a")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        hourly = self.weather_data.get("hourly", [])
        if hourly:
            temps = []
            times = []
            for h in hourly:
                try:
                    temps.append(float(h.get("temp", 0)))
                except (ValueError, TypeError):
                    temps.append(0)
                fx_time = h.get("fxTime", "")
                times.append(fx_time[11:16] if len(fx_time) >= 16 else "")

            x = list(range(len(temps)))
            ax.plot(x, temps, color="#89b4fa", linewidth=2, marker="o", markersize=3)
            ax.fill_between(x, temps, alpha=0.15, color="#89b4fa")
            ax.set_xticks(x[::3])
            ax.set_xticklabels(times[::3], rotation=45, fontsize=8)
            ax.set_ylabel("温度 (°C)", color="#cdd6f4", fontsize=10)
            ax.set_title("24 小时温度趋势", color="#cdd6f4", fontsize=12)
            fig.tight_layout()
        else:
            ax.text(0.5, 0.5, "暂无数据", ha="center", va="center",
                    color="#6c7086", transform=ax.transAxes, fontsize=14)

        return FigureCanvas(fig)

    def _create_forecast_item(self, day):
        """创建 7 天预报中的单日条目"""
        widget = QFrame()
        widget.setStyleSheet(
            "QFrame { background-color: #313244; border-radius: 8px; padding: 8px; }"
        )
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)

        # 日期
        date_str = day.get("fxDate", "")
        date_label = QLabel(date_str)
        date_label.setStyleSheet("font-size: 14px; color: #cdd6f4; min-width: 100px;")
        layout.addWidget(date_label)

        # 温度
        temp_str = f"{day.get('tempMax', '--')}° / {day.get('tempMin', '--')}°"
        temp_label = QLabel(temp_str)
        temp_label.setStyleSheet("font-size: 14px; color: #89b4fa; font-weight: bold; min-width: 100px;")
        layout.addWidget(temp_label)

        # 天气
        weather_str = f"白天: {day.get('textDay', '--')}  夜间: {day.get('textNight', '--')}"
        weather_label = QLabel(weather_str)
        weather_label.setStyleSheet("font-size: 13px; color: #a6adc8;")
        layout.addWidget(weather_label)

        layout.addStretch()

        return widget
