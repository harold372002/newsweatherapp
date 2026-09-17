@echo off
chcp 65001 >nul
echo News Weather App - Build Tool
echo.
echo [1/4] Check Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)
echo.
echo [2/4] Install deps...
pip install -r requirements.txt
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Install failed
    pause
    exit /b 1
)
echo.
echo [3/4] Config API Keys...
python setup_api.py
echo.
echo [4/4] Build exe...
pyinstaller build.spec --noconfirm
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)
echo.
echo Build complete! exe: dist\NewsWeather.exe
pause
