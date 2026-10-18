# Ejecuta TP2_Laboratorio_RAG_Agente.ipynb de punta a punta y guarda las salidas en el mismo archivo.
$ErrorActionPreference = 'Continue'
$proyecto = Split-Path $PSScriptRoot -Parent
Set-Location $proyecto
$venvPython = Join-Path $proyecto '.venv\Scripts\python.exe'
$log = Join-Path $proyecto 'ejecucion_log.txt'
$env:PYTHONIOENCODING = 'utf-8'
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'
$env:TRANSFORMERS_VERBOSITY = 'error'

if (-not (Test-Path $venvPython)) { Write-Host 'Falta el entorno .venv: ejecutar primero instalar.bat' -ForegroundColor Red; exit 1 }
try { Invoke-RestMethod -Uri 'http://localhost:11434/api/version' -TimeoutSec 3 | Out-Null }
catch {
    $app = @((Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama app.exe')) + (Get-PSDrive -PSProvider FileSystem | ForEach-Object { Join-Path $_.Root 'Ollama\ollama app.exe' }) |
        Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($app) { Start-Process -FilePath $app; Start-Sleep -Seconds 10 }
}

$inicio = Get-Date
"Inicio: $inicio" | Set-Content -Path $log -Encoding UTF8
Write-Host 'Ejecutando el notebook (15-30 minutos). No cierres esta ventana...' -ForegroundColor Cyan
& $venvPython -m jupyter nbconvert --to notebook --execute --inplace `
    --ExecutePreprocessor.timeout=1800 --ExecutePreprocessor.kernel_name=python3 `
    TP2_Laboratorio_RAG_Agente.ipynb 2>&1 | ForEach-Object { $linea = "$_"; Write-Host $linea; Add-Content -Path $log -Value $linea -Encoding UTF8 }
$codigo = $LASTEXITCODE
$minutos = [math]::Round(((Get-Date) - $inicio).TotalMinutes, 1)
if ($codigo -eq 0) { $mensaje = "OK: notebook ejecutado en $minutos minutos" ; $color = 'Green' }
else { $mensaje = "ERROR (codigo $codigo) despues de $minutos minutos: ver ejecucion_log.txt"; $color = 'Red' }
Add-Content -Path $log -Value $mensaje -Encoding UTF8
Write-Host $mensaje -ForegroundColor $color
