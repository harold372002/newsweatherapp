# -*- coding: utf-8 -*-
"""
语音播报引擎封装
基于 pyttsx3，在独立线程中运行，避免阻塞 UI
支持：播报、暂停、继续、停止
"""
import sys
import re
import queue
import threading

import pyttsx3
from PyQt6.QtCore import QObject, pyqtSignal as Signal


class TTSEngine(QObject):
    """
    语音播报引擎
    - 在独立线程中初始化 pyttsx3 并执行播报
    - 支持暂停 / 继续 / 停止
    - 通过 Qt 信号通知 UI 播报进度
    """

    # ── 信号 ──
    speak_started = Signal(str)       # 开始播报某段文本，参数为 text_id
    speak_finished = Signal(str)      # 某段文本播报结束
    sentence_started = Signal(str, int)  # 开始播报某句，参数为 (text_id, sentence_index)

    def __init__(self):
        super().__init__()
        self._voices = []
        self._rate = 200               # 默认语速（WPM）
        self._voice_id = None          # 指定音色 ID
        self._text_queue = queue.Queue()
        self._stop_flag = False
        self._pause_event = threading.Event()
        self._pause_event.set()        # set = 未暂停；clear = 已暂停
        self._running = False
        self._thread = None

        # 在主线程中获取可用音色列表
        self._init_voices()

    # ────────────── 音色列表 ──────────────

    def _init_voices(self):
        """在主线程中初始化一个临时引擎以获取音色列表"""
        try:
            if sys.platform == "win32":
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except ImportError:
                    pass
            tmp = pyttsx3.init()
            self._voices = tmp.getProperty("voices")
            del tmp
            if sys.platform == "win32":
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except ImportError:
                    pass
        except Exception:
            self._voices = []

    def get_voices(self):
        """获取系统可用音色列表"""
        return self._voices

    def get_chinese_voices(self):
        """筛选中文音色"""
        cn = []
        for v in self._voices:
            name = (v.name if hasattr(v, "name") else str(v)).lower()
            vid = (v.id if hasattr(v, "id") else "").lower()
            if any(kw in name or kw in vid for kw in ["chinese", "zh", "中文", "huihui", "yaoyao", "kangkang"]):
                cn.append(v)
        return cn if cn else list(self._voices)

    # ────────────── 参数设置 ──────────────

    def set_rate(self, multiplier):
        """设置语速倍率（0.5~2.0），映射到 pyttsx3 rate"""
        self._rate = int(200 * multiplier)

    def set_voice(self, voice_id):
        """设置音色 ID"""
        self._voice_id = voice_id

    # ────────────── 播报控制 ──────────────

    def speak(self, text, text_id=""):
        """
        播报一段文本
        :param text: 要播报的文本
        :param text_id: 文本标识，用于信号回调
        """
        self.stop()  # 先停止当前播报
        self._text_queue.put((text, text_id))
        if not self._running:
            self._start_thread()

    def pause(self):
        """暂停播报"""
        self._pause_event.clear()

    def resume(self):
        """继续播报"""
        self._pause_event.set()

    def stop(self):
        """停止播报"""
        self._stop_flag = True
        self._pause_event.set()  # 解除暂停以让线程退出等待
        # 清空队列
        while not self._text_queue.empty():
            try:
                self._text_queue.get_nowait()
            except queue.Empty:
                break
        self._text_queue.put((None, None))  # 发送停止信号

    def is_running(self):
        """是否正在播报"""
        return self._running

    # ────────────── 线程 ──────────────

    def _start_thread(self):
        """启动 TTS 线程"""
        self._running = True
        self._stop_flag = False
        self._pause_event.set()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """TTS 线程主循环"""
        # Windows 下需要初始化 COM
        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except ImportError:
                pass

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self._rate)
            if self._voice_id:
                try:
                    engine.setProperty("voice", self._voice_id)
                except Exception:
                    pass
        except Exception:
            self._running = False
            return

        while self._running:
            try:
                text, text_id = self._text_queue.get(timeout=0.3)
            except queue.Empty:
                continue

            if text is None:  # 停止信号
                break

            self.speak_started.emit(text_id)

            # 将文本拆分为句子，逐句播报以便支持暂停/停止
            sentences = self._split_sentences(text)
            for i, sentence in enumerate(sentences):
                if self._stop_flag:
                    break
                # 等待暂停解除
                self._pause_event.wait()
                if self._stop_flag:
                    break

                self.sentence_started.emit(text_id, i)
                try:
                    engine.say(sentence)
                    engine.runAndWait()
                except Exception:
                    break

            self.speak_finished.emit(text_id)

        # 清理
        try:
            engine.stop()
            del engine
        except Exception:
            pass

        if sys.platform == "win32":
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except ImportError:
                pass

        self._running = False

    def _split_sentences(self, text):
        """将文本拆分为句子"""
        # 按中英文标点分割
        parts = re.split(r"[。！？.!?；;\n]+", text)
        return [p.strip() for p in parts if p.strip()]

    def shutdown(self):
        """关闭引擎，等待线程结束"""
        self.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
