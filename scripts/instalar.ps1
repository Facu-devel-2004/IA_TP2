# Instalador del entorno del TP2: Python 3.12, Ollama + qwen2.5:7b y librerias de Python.
# Se ejecuta desde instalar.bat. Todo lo que muestra queda registrado en instalar_log.txt.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$proyecto = Split-Path $PSScriptRoot -Parent
Set-Location $proyecto
Start-Transcript -Path (Join-Path $proyecto 'instalar_log.txt') -Force | Out-Null
$MODELO = 'qwen2.5:7b'
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = '1'

function Paso([string]$texto) { Write-Host ''; Write-Host "==> $texto" -ForegroundColor Cyan }
function Ejecutar([string]$exe, [string[]]$argumentos) {
    # Ejecuta un programa externo, registra su salida y devuelve el codigo de salida.
    & $exe @argumentos 2>&1 | ForEach-Object { "$_" } | Out-Host
    return $LASTEXITCODE
}
function OllamaActivo {
    try { Invoke-RestMethod -Uri 'http://localhost:11434/api/version' -TimeoutSec 3 | Out-Null; return $true }
    catch { return $false }
}

$resultado = 'ERROR'
try {
    # 1. Espacio en disco: Ollama (~4 GB) + modelo (~4.7 GB) van al disco con mas espacio si C: no alcanza.
    Paso 'Revisando espacio en disco'
    $discos = Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' |
        Select-Object DeviceID, @{n = 'LibreGB'; e = { [math]::Round($_.FreeSpace / 1GB, 1) } }
    $discos | Format-Table -AutoSize | Out-String | Write-Host
    $libreC = ($discos | Where-Object { $_.DeviceID -eq 'C:' }).LibreGB
    $otro = $discos | Where-Object { $_.DeviceID -ne 'C:' } | Sort-Object LibreGB -Descending | Select-Object -First 1
    $carpetaOllama = $null
    $ollamaInstalado = [bool](Get-Command ollama -ErrorAction SilentlyContinue)
    if (-not $ollamaInstalado) {
        if ($libreC -ge 14) { Write-Host 'Ollama y el modelo se instalan en C:.' }
        elseif ($otro -and $otro.LibreGB -ge 12) {
            $carpetaOllama = "$($otro.DeviceID)\Ollama"
            Write-Host "C: tiene poco espacio: Ollama y el modelo se instalan en $carpetaOllama"
        }
        else { throw 'No hay espacio suficiente: hacen falta ~14 GB libres en C: o ~12 GB en otro disco.' }
    }
    if ($libreC -lt 4) { throw 'C: necesita al menos 4 GB libres para Python y sus librerias.' }

    # 2. Python 3.12 (instalacion de usuario, no requiere administrador)
    Paso 'Python 3.12'
    $python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
    if (-not (Test-Path $python)) {
        Ejecutar 'winget' @('install', '-e', '--id', 'Python.Python.3.12', '--source', 'winget', '--scope', 'user', '--silent',
            '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity') | Out-Null
    }
    if (-not (Test-Path $python)) { throw "No se encontro Python en $python despues de instalarlo." }
    Ejecutar $python @('--version') | Out-Null

    # 3. Ollama
    Paso 'Ollama'
    if ($ollamaInstalado) {
        $ollama = (Get-Command ollama).Source
    }
    else {
        $argumentos = @('install', '-e', '--id', 'Ollama.Ollama', '--source', 'winget', '--silent',
            '--accept-package-agreements', '--accept-source-agreements', '--disable-interactivity')
        if ($carpetaOllama) {
            # Los modelos se guardan junto a Ollama (variable de usuario OLLAMA_MODELS)
            $carpetaModelos = Join-Path $carpetaOllama 'models'
            New-Item -ItemType Directory -Force -Path $carpetaModelos | Out-Null
            [Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $carpetaModelos, 'User')
            $env:OLLAMA_MODELS = $carpetaModelos
            $argumentos += @('--location', $carpetaOllama)
        }
        Ejecutar 'winget' $argumentos | Out-Null
        # Ubicacion real (si winget ignoro --location, queda en la carpeta por defecto)
        $candidatos = @(Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe')
        if ($carpetaOllama) { $candidatos = @(Join-Path $carpetaOllama 'ollama.exe') + $candidatos }
        $ollama = $candidatos | Where-Object { Test-Path $_ } | Select-Object -First 1
    }
    if (-not $ollama -or -not (Test-Path $ollama)) { throw 'No se encontro ollama.exe despues de instalarlo.' }
    Write-Host "Ollama instalado en: $ollama" 
    if (-not (OllamaActivo)) {
        $app = Join-Path (Split-Path $ollama) 'ollama app.exe'
        if (Test-Path $app) { Start-Process -FilePath $app } else { Start-Process -FilePath $ollama -ArgumentList 'serve' -WindowStyle Hidden }
        for ($i = 0; $i -lt 30 -and -not (OllamaActivo); $i++) { Start-Sleep -Seconds 2 }
    }
    if (-not (OllamaActivo)) { throw 'Ollama no responde en http://localhost:11434' }
    Write-Host "Ollama activo: $((Invoke-RestMethod 'http://localhost:11434/api/version').version)"

    # 4. Modelo de lenguaje (se muestra la barra de progreso; no se registra en el log)
    Paso "Descargando el modelo $MODELO (~4.7 GB, puede tardar varios minutos)"
    & $ollama pull $MODELO
    if ($LASTEXITCODE -ne 0) { throw "Fallo 'ollama pull $MODELO'." }

    # 5. Entorno virtual y librerias
    Paso 'Entorno virtual .venv y librerias de Python (~1.5 GB)'
    $venvPython = Join-Path $proyecto '.venv\Scripts\python.exe'
    if (-not (Test-Path $venvPython)) { Ejecutar $python @('-m', 'venv', (Join-Path $proyecto '.venv')) | Out-Null }
    Ejecutar $venvPython @('-m', 'pip', 'install', '--upgrade', 'pip', '--no-cache-dir', '--disable-pip-version-check') | Out-Null
    $codigo = Ejecutar $venvPython @('-m', 'pip', 'install', '--no-cache-dir', '--disable-pip-version-check',
        '-r', (Join-Path $proyecto 'requirements.txt'))
    if ($codigo -ne 0) { throw 'Fallo la instalacion de librerias (ver mensajes de pip arriba).' }

    # 6. Modelos de embeddings (se descargan una vez desde Hugging Face)
    Paso 'Descargando modelos de embeddings'
    $codigo = Ejecutar $venvPython @('-c', "from sentence_transformers import SentenceTransformer as S; S('intfloat/multilingual-e5-small'); S('sentence-transformers/all-MiniLM-L6-v2'); print('embeddings ok')")
    if ($codigo -ne 0) { throw 'Fallo la descarga de los modelos de embeddings.' }

    # 7. Resumen
    Paso 'Resumen'
    Ejecutar $venvPython @('-c', "import sys, langchain, langchain_ollama, faiss, sentence_transformers as st; print('Python', sys.version.split()[0], '| langchain', langchain.__version__, '| sentence-transformers', st.__version__, '| faiss', faiss.__version__)") | Out-Null
    Ejecutar $ollama @('list') | Out-Null
    $resultado = 'OK'
    Write-Host ''
    Write-Host 'INSTALACION COMPLETA. Ya se puede ejecutar ejecutar_notebook.bat' -ForegroundColor Green
}
catch {
    Write-Host ''
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    $resultado = "ERROR: $($_.Exception.Message)"
}
finally {
    Set-Content -Path (Join-Path $proyecto 'instalar_resultado.txt') -Value $resultado -Encoding UTF8
    Stop-Transcript | Out-Null
}
