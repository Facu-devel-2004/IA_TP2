# Guía: instalación de Ollama y del modelo local

El agente usa un modelo de lenguaje que corre **en la propia computadora** mediante **Ollama**. No requiere claves de API ni conexión a internet para generar respuestas (sí para la herramienta que consulta GitHub en vivo).

> En Windows, `instalar.bat` hace todos estos pasos automáticamente. Esta guía es para instalarlo a mano o en Linux/macOS.

## 1. Modelo elegido

| Modelo | Descarga | RAM aprox. | Uso recomendado |
| :--- | :--- | :--- | :--- |
| `qwen2.5:7b` (por defecto) | 4,7 GB | 5,5 GB | Mejores respuestas y elección de herramientas más confiable |
| `qwen2.5:3b` | 1,9 GB | 2,5 GB | Equipos con 8 GB de RAM; unas 3 veces más rápido |

Ambos admiten *tool calling* (necesario para el agente). Sin placa de video, el modelo corre en el procesador: con `qwen2.5:7b` cada respuesta del agente tarda entre 1 y 4 minutos.

## 2. Instalar Ollama

* **Windows:** descargar el instalador de https://ollama.com/download/windows o ejecutar `winget install Ollama.Ollama`. Necesita unos 4 GB de disco. Para instalarlo en otro disco: `OllamaSetup.exe /DIR="D:\Ollama"`; para guardar los modelos en otra carpeta, crear la variable de entorno de usuario `OLLAMA_MODELS`.
* **Linux:** `curl -fsSL https://ollama.com/install.sh | sh`
* **macOS:** descargar desde https://ollama.com/download/mac o `brew install ollama`.

## 3. Descargar el modelo y verificar

```bash
ollama pull qwen2.5:7b
ollama list                      # debe aparecer qwen2.5:7b
ollama run qwen2.5:7b "Hola"     # prueba rápida (opcional)
```

Ollama queda escuchando en `http://localhost:11434`. Para usar otro modelo sin modificar el código: definir `OLLAMA_MODEL=qwen2.5:3b` antes de ejecutar el notebook o `agente_cli.py`.
