# -*- coding: utf-8 -*-
"""
core 包初始化
提供通用后台工作线程 Worker，供各 UI 模块复用
"""
from PyQt6.QtCore import QThread, pyqtSignal as Signal


class Worker(QThread):
    """通用后台工作线程，用于执行 API 调用等耗时操作，避免阻塞 UI"""

    result_ready = Signal(object)   # 任务完成信号，携带返回值
    error_occurred = Signal(str)   # 任务出错信号，携带错误信息

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._func(*self._args, **self._kwargs)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
