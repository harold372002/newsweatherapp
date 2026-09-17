# 新闻天气播报

一个集**新闻播报**与**天气查询**于一体的 Windows 桌面应用，使用 Python + PyQt6 开发，支持语音播报、横屏适配，可打包为单个 .exe 双击运行。

## 功能概览

| 模块 | 功能 |
|------|------|
| 主窗口 | 天气卡片 + 头条轮播（5秒自动切换）+ 新闻分类 Tab（头条/科技/体育/财经/娱乐）|
| 天气详情 | 当前天气大卡片 + 24小时温度趋势图（matplotlib）+ 7天预报列表 |
| 新闻详情 | 点击新闻弹出详情窗口，显示标题/来源/时间/正文，支持播放/暂停/停止朗读 |
| 设置 | 默认城市搜索、语速滑块（0.5x~2.0x）、音色选择、播报模式（天气/新闻/混合）、API Key 配置 |
| 语音播报 | pyttsx3 调用 Windows 系统 TTS，独立线程运行，播报时高亮当前条目 |

## 技术栈

- **语言**：Python 3.11
- **GUI**：PyQt6
- **网络请求**：requests + QThread 后台线程（不阻塞 UI）
- **语音播报**：pyttsx3（调用 Windows SAPI5 TTS，离线可用）
- **图表**：matplotlib（嵌入 PyQt6）
- **配置存储**：JSON 文件 → `%USERPROFILE%\.newsweatherapp\config.json`
- **打包**：PyInstaller --onefile --windowed

## 项目结构

```
newsweatherapp/
├── main.py                  # 入口，启动主窗口
├── ui/
│   ├── __init__.py
│   ├── mainwindow.py        # 主窗口（Dashboard）
│   ├── weatherwidget.py     # 天气卡片 + 天气详情对话框
│   ├── newswidget.py        # 头条轮播 + 新闻分类 Tab + 新闻列表
│   ├── detaildialog.py      # 新闻详情弹窗
│   └── settingsdialog.py    # 设置窗口
├── core/
│   ├── __init__.py          # Worker 通用后台线程
│   ├── weatherapi.py        # 和风天气 API 封装
│   ├── newsapi.py           # 新闻 API 封装（NewsAPI / 聚合数据）
│   ├── ttsengine.py         # pyttsx3 语音播报封装
│   └── config.py            # 配置读写
├── resources/
│   ├── icon.ico             # 应用图标
│   └── style.qss            # 界面样式表（暗色主题）
├── requirements.txt
├── build.spec               # PyInstaller 配置
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd newsweatherapp
pip install -r requirements.txt
```

### 2. 配置 API Key

首次运行程序会自动在 `%USERPROFILE%\.newsweatherapp\` 下创建 `config.json`。

**方式一：通过设置界面配置**

运行程序后点击右上角「⚙ 设置」按钮，在 API 配置区域填入 Key。

**方式二：手动编辑配置文件**

编辑 `%USERPROFILE%\.newsweatherapp\config.json`：

```json
{
  "qweather_api_key": "你的和风天气Key",
  "newsapi_key": "你的新闻API Key",
  "news_provider": "newsapi"
}
```

#### 获取 API Key

| 服务 | 注册地址 | 免费额度 | 说明 |
|------|----------|----------|------|
| 和风天气 | https://dev.qweather.com/ | 每天 1000 次 | 创建应用获取 API Key |
| NewsAPI | https://newsapi.org/ | 每天 100 次 | 注册后在仪表盘获取 Key |
| 聚合数据 | https://www.juhe.cn/ | 每天 100 次 | 申请"新闻头条"接口 |

### 3. 运行

```bash
python main.py
```

### 4. 打包为 exe

```bash
pyinstaller build.spec
```

打包完成后，`dist/NewsWeather.exe` 即为最终可执行文件，双击即可运行，无需安装 Python。

> exe 大小约 40-50MB（含 PyQt6 + matplotlib + pyttsx3）。

## 使用说明

### 天气查询
- 主窗口顶部显示当前城市天气卡片（温度、体感、天气状况、湿度、风力、空气质量、更新时间）
- 点击天气卡片打开天气详情：24小时温度趋势图 + 7天预报

### 新闻浏览
- 中部头条轮播每 5 秒自动切换，点击可查看详情
- 底部 Tab 切换分类（头条/科技/体育/财经/娱乐）
- 点击任意新闻条目打开详情窗口，可朗读全文

### 语音播报
- 点击右上角「🔊 播报」按钮，按设置中的播报模式朗读
- 天气播报为自然口语化文案，如："北京今天晴，气温18到26度，空气质量良，适合外出。"
- 新闻播报读取标题摘要
- 播报时自动高亮当前正在读的条目
- 再次点击按钮可停止播报

### 设置
- 默认城市：输入城市名点击搜索，选择匹配结果
- 语速：0.5x ~ 2.0x
- 音色：从系统可用 TTS 音色中选择
- 播报模式：天气 / 新闻 / 混合

## 常见问题

**Q: 打包后 pyttsx3 报错怎么办？**
A: `build.spec` 已配置 `hiddenimports=['pyttsx3.drivers', 'pyttsx3.drivers.sapi5']`，如仍报错请确保安装了 `pywin32`。

**Q: 天气数据不显示？**
A: 请检查和风天气 API Key 是否正确，城市 ID 是否匹配。可在设置中搜索城市重新选择。

**Q: 新闻列表为空？**
A: 请检查新闻 API Key 是否正确，NewsAPI 免费版仅支持 localhost 请求（开发环境可用，生产环境需付费版）。

**Q: 没有声音？**
A: 请确保 Windows 系统已安装 TTS 语音包（设置 → 时间和语言 → 语音）。

## 开发信息

- Python 3.11+
- PyQt6 6.5+
- 代码注释为中文，关键逻辑均有注释
- 所有功能均已实现，无 TODO 占位
