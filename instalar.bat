@echo off
REM Instala todo lo necesario para el TP2: Python 3.12, Ollama, el modelo qwen2.5:7b
REM y las librerias de Python (en un entorno virtual .venv dentro de esta carpeta).
REM El detalle queda en instalar_log.txt.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\instalar.ps1"
echo.
pause
