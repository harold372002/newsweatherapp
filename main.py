# -*- coding: utf-8 -*-
"""
新闻天气播报 — 入口文件
启动 QApplication，加载样式表和配置，创建主窗口
"""
import sys
import os


def resource_path(relative_path):
    """
    获取资源文件绝对路径
    兼容开发环境和 PyInstaller 打包环境（sys._MEIPASS）
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境：项目根目录
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


def main():
    # 确保项目根目录在 sys.path 中（开发环境）
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from core.config import ConfigManager
    from ui.mainwindow import MainWindow

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("新闻天气播报")

    # 加载样式表
    qss_path = resource_path("resources/style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # 设置应用图标
    icon_path = resource_path("resources/icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 加载配置（首次运行自动创建）
    config = ConfigManager()

    # 创建并显示主窗口
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
