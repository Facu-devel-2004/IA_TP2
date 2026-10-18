@echo off
REM Abre el agente en modo conversacion (escribir "salir" para terminar).
cd /d "%~dp0"
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set TRANSFORMERS_VERBOSITY=error
".venv\Scripts\python.exe" agente_cli.py
pause
