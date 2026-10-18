@echo off
REM Ejecuta el notebook completo y guarda las salidas dentro del mismo archivo.
REM Tarda entre 15 y 30 minutos en una PC sin placa de video. El detalle queda en ejecucion_log.txt.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\ejecutar_notebook.ps1"
echo.
pause
