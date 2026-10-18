@echo off
REM Abre el notebook en el navegador con Jupyter (cerrar esta ventana para detenerlo).
cd /d "%~dp0"
".venv\Scripts\python.exe" -m notebook TP2_Laboratorio_RAG_Agente.ipynb
