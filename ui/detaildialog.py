# -*- coding: utf-8 -*-
"""
新闻详情对话框
显示新闻标题、来源、时间、正文
顶部有播放/暂停按钮，可朗读当前新闻
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from core import Worker


class NewsDetailDialog(QDialog):
    """新闻详情弹窗"""

    def __init__(self, news_item, news_api, tts_engine, parent=None):
        super().__init__(parent)
        self.news_item = news_item
        self.news_api = news_api
        self.tts = tts_engine
        self._tts_state = "stopped"  # stopped / playing / paused
        self._worker = None

        self._init_ui()
        self._load_content()

        # 连接 TTS 信号
        self.tts.speak_finished.connect(self._on_tts_finished)

    def _init_ui(self):
        self.setWindowTitle("新闻详情")
        self.resize(700, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ── 顶部栏：播放按钮 + 来源 ──
        top_bar = QHBoxLayout()
        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.setFixedSize(100, 36)
        self.play_btn.clicked.connect(self._toggle_play)
        top_bar.addWidget(self.play_btn)

        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.setFixedSize(80, 36)
        self.stop_btn.clicked.connect(self._stop_play)
        top_bar.addWidget(self.stop_btn)

        top_bar.addStretch()

        self.source_label = QLabel(self.news_item.get("source", ""))
        self.source_label.setStyleSheet("color: #6c7086; font-size: 12px;")
        top_bar.addWidget(self.source_label)
        layout.addLayout(top_bar)

        # ── 标题 ──
        self.title_label = QLabel(self.news_item.get("title", ""))
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #cdd6f4;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # ── 时间 ──
        self.time_label = QLabel(self.news_item.get("time", ""))
        self.time_label.setStyleSheet("color: #6c7086; font-size: 12px;")
        layout.addWidget(self.time_label)

        # ── 分隔线 ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #45475a; max-height: 1px;")
        layout.addWidget(sep)

        # ── 正文（可滚动）──
        self.content_label = QLabel("正在加载...")
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.content_label.setStyleSheet("font-size: 15px; color: #cdd6f4; line-height: 1.6;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.content_label)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(scroll, 1)

        # ── 底部按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _load_content(self):
        """加载新闻正文"""
        content = self.news_item.get("content", "")
        if content and len(content) > 50:
            self.content_label.setText(content)
        else:
            # 从 URL 抓取全文
            url = self.news_item.get("url", "")
            if url:
                self.content_label.setText("正在获取新闻全文...")
                self._worker = Worker(self.news_api.fetch_full_content, url)
                self._worker.result_ready.connect(self._on_content_loaded)
                self._worker.error_occurred.connect(
                    lambda e: self.content_label.setText(f"获取全文失败: {e}")
                )
                self._worker.start()
            else:
                self.content_label.setText("暂无内容")

    def _on_content_loaded(self, text):
        """全文加载完成"""
        self.content_label.setText(text)

    # ────────────── TTS 控制 ──────────────

    def _toggle_play(self):
        """切换播放/暂停"""
        if self._tts_state == "stopped":
            # 开始播放
            title = self.news_item.get("title", "")
            content = self.content_label.text()
            text = f"{title}。{content}"
            self.tts.speak(text, "news_detail")
            self._tts_state = "playing"
            self.play_btn.setText("⏸ 暂停")
        elif self._tts_state == "playing":
            # 暂停
            self.tts.pause()
            self._tts_state = "paused"
            self.play_btn.setText("▶ 继续")
        elif self._tts_state == "paused":
            # 继续
            self.tts.resume()
            self._tts_state = "playing"
            self.play_btn.setText("⏸ 暂停")

    def _stop_play(self):
        """停止播放"""
        self.tts.stop()
        self._tts_state = "stopped"
        self.play_btn.setText("▶ 播放")

    def _on_tts_finished(self, text_id):
        """TTS 播报结束回调"""
        if text_id == "news_detail":
            self._tts_state = "stopped"
            self.play_btn.setText("▶ 播放")

    def closeEvent(self, event):
        """关闭时停止 TTS"""
        self.tts.stop()
        # 断开信号
        try:
            self.tts.speak_finished.disconnect(self._on_tts_finished)
        except TypeError:
            pass
        super().closeEvent(event)
