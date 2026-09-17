# -*- coding: utf-8 -*-
"""
新闻列表 + 头条轮播
- HeadlineCarousel：自动切换的头条轮播（5 秒一张）
- NewsItemWidget：单条新闻条目控件
- NewsTabWidget：分类 Tab + 新闻列表
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QListWidget, QListWidgetItem, QTabWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize


class HeadlineCarousel(QFrame):
    """头条轮播控件，每 5 秒自动切换"""

    clicked = pyqtSignal(dict)  # 点击信号，携带当前头条数据

    def __init__(self):
        super().__init__()
        self.setObjectName("carouselFrame")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(80)
        self.setMaximumHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._headlines = []
        self._current_index = 0
        self._highlight_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(4)

        # ── 顶部：标签 + 计数器 ──
        header = QHBoxLayout()
        tag = QLabel("📌 今日头条")
        tag.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #f9e2af; "
            "background-color: #4a3520; padding: 2px 8px; border-radius: 4px;"
        )
        header.addWidget(tag)
        header.addStretch()
        self.counter_label = QLabel("")
        self.counter_label.setStyleSheet("font-size: 12px; color: #6c7086;")
        header.addWidget(self.counter_label)
        layout.addLayout(header)

        # ── 标题 ──
        self.title_label = QLabel("暂无头条新闻")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #cdd6f4;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # ── 来源 + 时间 ──
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("font-size: 12px; color: #6c7086;")
        layout.addWidget(self.info_label)

        # ── 自动切换定时器 ──
        self._timer = QTimer()
        self._timer.timeout.connect(self._next)
        self._timer.start(5000)

    def set_headlines(self, headlines):
        """设置头条列表"""
        self._headlines = headlines
        self._current_index = 0
        self._highlight_index = -1
        if headlines:
            self._update_display()
            self._timer.start(5000)
        else:
            self.title_label.setText("暂无头条新闻")
            self.info_label.setText("")
            self.counter_label.setText("")
            self._timer.stop()

    def set_highlight(self, index):
        """高亮指定索引（用于播报时标记当前条目）"""
        self._highlight_index = index
        self._update_display()

    def _next(self):
        """切换到下一条"""
        if not self._headlines:
            return
        self._current_index = (self._current_index + 1) % len(self._headlines)
        self._update_display()

    def _update_display(self):
        """更新显示内容"""
        if not self._headlines:
            return
        item = self._headlines[self._current_index]
        self.title_label.setText(item.get("title", ""))

        source = item.get("source", "")
        time_str = item.get("time", "")
        self.info_label.setText(f"{source}  ·  {time_str}")
        self.counter_label.setText(f"{self._current_index + 1}/{len(self._headlines)}")

        # 高亮效果
        if self._highlight_index == self._current_index:
            self.setStyleSheet(
                "QFrame#carouselFrame { background-color: #3b3550; border-radius: 10px; "
                "border-left: 3px solid #89b4fa; }"
            )
        else:
            self.setStyleSheet("")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._headlines:
            self.clicked.emit(self._headlines[self._current_index])
        super().mousePressEvent(event)


class NewsItemWidget(QWidget):
    """单条新闻条目控件"""

    def __init__(self, news_item):
        super().__init__()
        self.news_item = news_item
        self._highlighted = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self.title_label = QLabel(news_item.get("title", ""))
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #cdd6f4;")
        self.title_label.setWordWrap(True)

        source = news_item.get("source", "")
        time_str = news_item.get("time", "")
        self.info_label = QLabel(f"{source}  ·  {time_str}")
        self.info_label.setStyleSheet("font-size: 12px; color: #6c7086;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.info_label)

    def set_highlight(self, highlighted):
        """设置高亮状态"""
        self._highlighted = highlighted
        if highlighted:
            self.setStyleSheet(
                "background-color: #3b3550; border-left: 3px solid #89b4fa;"
            )
        else:
            self.setStyleSheet("")


class NewsTabWidget(QTabWidget):
    """分类 Tab + 新闻列表"""

    news_clicked = pyqtSignal(dict)  # 点击新闻条目信号

    # 分类配置：(显示名, 数据 key)
    CATEGORIES = [
        ("头条", "top"),
        ("科技", "technology"),
        ("体育", "sports"),
        ("财经", "business"),
        ("娱乐", "entertainment"),
    ]

    def __init__(self):
        super().__init__()
        self._lists = {}       # key -> QListWidget
        self._items = {}       # key -> [QListWidgetItem, ...]
        self._data = {}        # key -> [news_dict, ...]

        for name, key in self.CATEGORIES:
            list_widget = QListWidget()
            list_widget.setAlternatingRowColors(False)
            list_widget.itemClicked.connect(lambda item, k=key: self._on_item_clicked(item, k))
            self._lists[key] = list_widget
            self._items[key] = []
            self.addTab(list_widget, name)

    def update_news(self, data):
        """更新所有分类的新闻数据"""
        self._data = data
        for key, list_widget in self._lists.items():
            list_widget.clear()
            self._items[key] = []
            articles = data.get(key, [])
            for article in articles:
                item_widget = NewsItemWidget(article)
                item = QListWidgetItem()
                item.setSizeHint(QSize(0, 70))
                item.setData(Qt.ItemDataRole.UserRole, article)
                list_widget.addItem(item)
                list_widget.setItemWidget(item, item_widget)
                self._items[key].append(item)

    def _on_item_clicked(self, item, category):
        """点击新闻条目"""
        article = item.data(Qt.ItemDataRole.UserRole)
        if article:
            self.news_clicked.emit(article)

    def show_message(self, msg):
        """显示提示信息"""
        for list_widget in self._lists.values():
            list_widget.clear()
            item = QListWidgetItem(msg)
            list_widget.addItem(item)

    def highlight_item(self, category, index):
        """高亮指定分类中指定索引的新闻条目"""
        items = self._items.get(category, [])
        # 先清除所有高亮
        for it in items:
            widget = self._lists[category].itemWidget(it)
            if isinstance(widget, NewsItemWidget):
                widget.set_highlight(False)
        # 高亮指定条目
        if 0 <= index < len(items):
            widget = self._lists[category].itemWidget(items[index])
            if isinstance(widget, NewsItemWidget):
                widget.set_highlight(True)
                # 滚动到该条目
                self._lists[category].scrollToItem(items[index])
