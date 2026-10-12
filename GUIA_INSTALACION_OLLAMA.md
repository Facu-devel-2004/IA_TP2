# Guía Rápida: Instalación y Configuración de Ollama (Modelo Local)

Esta guía explica paso a paso cómo instalar **Ollama** y descargar el modelo local **`qwen2.5:1.5b`** para ejecutar el pipeline de RAG y el Agente de este Trabajo de Laboratorio sin depender de claves de API externas (como OpenAI o Hugging Face) ni conexiones de red para la inferencia.

---

## 1. ¿Por qué usamos este modelo?
* **Modelo:** `qwen2.5:1.5b` (1.5 mil millones de parámetros).
* **Tamaño en disco:** ~986 MB.
* **Consumo de memoria:** ~1.5 GB de RAM / VRAM.
* **Ventajas:** Funciona de forma muy fluida en cualquier computadora (CPU estándar o placa gráfica), tiene soporte nativo para *Tool Calling* (llamada a herramientas del Agente) y es 100% gratuito y privado.

---

## 2. Instalación de Ollama

Elegí las instrucciones correspondientes a tu sistema operativo:

### 🐧 Linux (Ubuntu, Debian, Arch, Fedora, etc.)
Abrí una terminal y ejecutá:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
*Ollama se instalará y se iniciará automáticamente como servicio del sistema.*

Si necesitás verificar el estado del servicio:
```bash
systemctl status ollama
```

---

### 🪟 Windows
1. Descargá el instalador oficial desde [https://ollama.com/download/windows](https://ollama.com/download/windows).
2. Ejecutá el archivo `OllamaSetup.exe` y seguí las instrucciones en pantalla.
3. Al finalizar, Ollama se ejecutará automáticamente en la bandeja del sistema (ícono junto al reloj).

---

### 🍏 macOS
1. Descargá el instalador desde [https://ollama.com/download/mac](https://ollama.com/download/mac) o instalalo con Homebrew:
```bash
brew install ollama
```
2. Ejecutá la aplicación Ollama desde la carpeta Aplicaciones.

---

## 3. Descarga del Modelo `qwen2.5:1.5b`

Una vez instalado Ollama, abrí tu terminal (en Windows podés usar PowerShell o CMD) y ejecutá el siguiente comando para descargar el modelo:

```bash
ollama pull qwen2.5:1.5b
```

*(Opcional)* Si querés probarlo directamente en la terminal para chatear con él:
```bash
ollama run qwen2.5:1.5b
```
*(Para salir de la consola de chat de Ollama, escribí `/bye`).*

---

## 4. Verificación de Funcionamiento

1. **Listar modelos instalados:**
   ```bash
   ollama list
   ```
   Deberías ver una salida similar a:
   ```text
   NAME            ID              SIZE      MODIFIED
   qwen2.5:1.5b    65ec06548149    986 MB    ...
   ```

2. **Verificar que la API local esté escuchando:**
   Abrí tu navegador web o ejecutá en la terminal:
   ```bash
   curl http://localhost:11434
   ```
   Debe responder:
   ```text
   Ollama is running
   ```

---

## 5. Librerías de Python Requeridas en el Proyecto

Para conectar el notebook con tu Ollama local, asegurate de tener instaladas las dependencias de LangChain en tu entorno virtual:

```bash
pip install -q langchain langchain-community langchain-ollama langchain-openai
```

El notebook se conectará automáticamente al endpoint local `http://localhost:11434`.
