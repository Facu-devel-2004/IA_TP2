# Trabajo de Laboratorio N° 2 — Agente Inteligente con RAG
**Inteligencia Artificial – Sistemas Inteligentes (FCEFyN – UNC)** · NLP, representaciones vectoriales, LLMs, RAG y agentes

Agente basado en un LLM local que responde preguntas sobre la **API REST de GitHub** fundamentándose en un corpus técnico (RAG). También puede **consultar datos en vivo** de repositorios reales y **calcular el consumo de cuota** (rate limit) de la API.

## Arquitectura

```
                         ┌──────────────────────────────────────────┐
  Pregunta del usuario ─►│  Agente ReAct (LangChain create_agent)    │─► Respuesta integrada
                         │  LLM: qwen2.5:7b local (Ollama)           │   y fundamentada
                         └──────┬──────────────┬──────────────┬──────┘
                                │ tool call    │ tool call    │ tool call
                                ▼              ▼              ▼
              consultar_documentacion  consultar_repositorio  calcular_cuota
                  (RAG)                  (API GitHub en vivo)   (cálculo)
                    │
       corpus/*.md → limpieza → chunks por encabezado → FAISS (e5) + BM25 → fusión RRF (top-4)
```

| Etapa | Decisión |
| :--- | :--- |
| Corpus | 4 documentos Markdown sobre la API REST de GitHub (`corpus/`) |
| Limpieza | Normalización de saltos de línea, sin separadores `---`, negritas ni líneas vacías repetidas |
| Segmentación | `MarkdownHeaderTextSplitter` (por `#`/`##`/`###`) + una sección (endpoint) por chunk; `RecursiveCharacterTextSplitter` sólo si supera 1500 caracteres; ruta de encabezados antepuesta a cada chunk |
| Embeddings | `intfloat/multilingual-e5-small` (multilingüe, 384 dimensiones, prefijos `query:`/`passage:`) |
| Base vectorial | FAISS `IndexFlatIP`; vectores normalizados → similitud coseno exacta |
| Búsqueda | Híbrida: semántica (FAISS) + léxica (BM25), 10 candidatos cada una, fusionadas con Reciprocal Rank Fusion; top-4 |
| LLM | `qwen2.5:7b` vía Ollama, temperatura 0, contexto de 8192 tokens |
| Agente | `langchain.agents.create_agent` con 3 herramientas (*tool calling*, ciclo ReAct) |

## Estructura

```text
IA_TP2/
├── TP2_Laboratorio_RAG_Agente.ipynb   # Entregable principal: pipeline completo con salidas
├── Informe_Tecnico_TP2.pdf           # Informe técnico (2 páginas); también en .docx
├── agente_cli.py                      # Mismo agente en modo conversación por consola
├── requirements.txt                   # Dependencias de Python
├── corpus/                            # Base de conocimientos (4 documentos + README)
├── faiss_github_api_index/            # Índice FAISS generado por el notebook
├── resultados_interaccion.json        # Registro de las consultas de prueba (generado por el notebook)
├── instalar.bat                       # Windows: instala Python, Ollama, el modelo y las librerías
├── ejecutar_notebook.bat              # Windows: ejecuta el notebook completo y guarda las salidas
├── iniciar_agente.bat                 # Windows: abre el agente en modo conversación
├── abrir_notebook.bat                 # Windows: abre el notebook en Jupyter
├── scripts/                           # Scripts de PowerShell usados por los .bat
└── GUIA_INSTALACION_OLLAMA.md         # Instalación manual de Ollama (cualquier sistema)
```

## Cómo ejecutarlo

**Windows (automático):** doble clic en `instalar.bat` (una sola vez), después en `ejecutar_notebook.bat` o `iniciar_agente.bat`.

**Manual (cualquier sistema):**

```bash
# 1. Instalar Ollama (https://ollama.com/download) y descargar el modelo
ollama pull qwen2.5:7b

# 2. Crear un entorno e instalar dependencias (Python 3.10 a 3.12)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Ejecutar
jupyter notebook TP2_Laboratorio_RAG_Agente.ipynb
python agente_cli.py                              # modo conversación
python agente_cli.py "¿Cómo creo un issue?"       # una sola pregunta
```

Variables de entorno opcionales: `OLLAMA_MODEL` (otro modelo, por ejemplo `qwen2.5:3b` en equipos con poca RAM), `OLLAMA_BASE_URL` y `GITHUB_TOKEN` (eleva la cuota de la API de GitHub de 60 a 5000 solicitudes por hora).

## Herramientas del agente

| Herramienta | Tipo | Descripción |
| :--- | :--- | :--- |
| `consultar_documentacion_github(consulta)` | RAG | Recupera los 4 fragmentos más relevantes del corpus (búsqueda híbrida), con su archivo de origen. |
| `consultar_repositorio_github(owner, repo)` | Búsqueda externa en vivo | `GET /repos/{owner}/{repo}` + `GET /search/issues` para separar issues y pull requests abiertos (el campo `open_issues_count` los suma). |
| `calcular_cuota_rate_limit(solicitudes_por_hora, autenticado)` | Cálculo | Límite (60 o 5000/h), porcentaje consumido, restantes o excedentes e intervalo mínimo entre solicitudes. |

## Resultados (ejecución del 17/10/2026, `qwen2.5:7b` en CPU)

Evaluación del recuperador con 16 preguntas parafraseadas (k = 4):

| Método de búsqueda | Hit@1 | Hit@4 | MRR |
| :--- | :---: | :---: | :---: |
| Semántica `all-MiniLM-L6-v2` (inglés) | 0,38 | 0,62 | 0,48 |
| Semántica `multilingual-e5-small` | 0,69 | 0,94 | 0,78 |
| Léxica BM25 | 0,75 | 0,94 | 0,83 |
| **Híbrida e5 + BM25 (RRF)** | **0,88** | **0,94** | **0,89** |

Consultas de prueba del agente (detalle completo en la sección 10 del notebook y en `resultados_interaccion.json`):

| Caso | Herramientas usadas | Resultado |
| :--- | :--- | :--- |
| 1. Cabeceras recomendadas y falta de `User-Agent` | Documentación | Las 4 cabeceras; sin `User-Agent` → 403 |
| 2. 80 solicitudes/h con y sin token | Cálculo ×2 + documentación | Sin token excede 60/h (133,3 %); con token 1,6 % de 5000/h; 429 al exceder |
| 3. Métricas de `facebook/react` | Repositorio en vivo | Estrellas, forks, 880 issues y 579 PRs abiertos, JavaScript |
| 4. Crear un issue + issues abiertos de `facebook/react` | Documentación + repositorio en vivo | `POST /repos/{owner}/{repo}/issues`, `title` obligatorio, 880 issues |
| 5. Webhooks (fuera del corpus) | Documentación | Indica que el corpus no lo cubre (no inventa) |

El informe técnico (`Informe_Tecnico_TP2.pdf`) resume la metodología, las decisiones de diseño y estos resultados.
