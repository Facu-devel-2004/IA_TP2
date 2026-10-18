# Bitácora y Contexto para la Próxima Sesión de IA

> **DOCUMENTO PARA EL ASISTENTE DE IA:**  
> Lee este archivo antes de continuar con el desarrollo de este repositorio. Contiene el estado exacto del proyecto, las decisiones de diseño arquitectónico tomadas, y las tareas inmediatas pendientes para completar el Trabajo de Laboratorio N° 2.

---

## 1. Contexto Académico
* **Materia:** Inteligencia Artificial – Sistemas Inteligentes (FCEFyN).
* **Consigna Principal:** [Trabajo de laboratorio 2 - Consignas.pdf](Trabajo%20de%20laboratorio%202%20-%20Consignas.pdf).
* **Temas Involucrados:** NLP, Representaciones Vectoriales, LLMs, RAG y Agentes Autónomos.
* **Módulos de Referencia de la Cátedra:**
  * Módulo 14: Transformers, Embeddings y RAG (`14.Transformers/RAG_notebook_2026_2.ipynb`).
  * Módulo 15: Word2Vec y embeddings (`15_text_w2v_img_mlp_kmeans`).
  * Módulo 17: Agentes ReAct y LangChain (`17_Agentes/Agente_LangChain.ipynb` y `Agente_ReAct.ipynb`).

---

## 2. Decisiones de Diseño Tomadas

1. **Dominio Técnico Seleccionado:** **GitHub REST API (v3 / versión 2022-11-28)**.
   * *Razón:* Es un dominio formal, estructurado y acotado, ideal para RAG porque los LLMs suelen alucinar parámetros o rutas exactas de endpoints.
2. **Corpus de Documentación (`corpus/`):**
   * `01_autenticacion_y_rate_limits.md`: Base URL, cabeceras recomendadas (`User-Agent` como única estrictamente obligatoria, `Authorization`, `Accept`, `X-GitHub-Api-Version`), cuotas (60/5000 req/h) y códigos HTTP (incluyendo `403` y `429 Too Many Requests`).
   * `02_repositorios_y_ramas.md`: Endpoints de creación, listado, configuración de repositorios, branches y releases.
   * `03_issues_y_etiquetas.md`: Endpoints de issues, filtros (`state`, `sort`), creación, comentarios, conteo separado de issues/PRs vía Search API (`GET /search/issues`) y labels.
   * `04_pull_requests_y_revisiones.md`: Endpoints de PRs, métodos de merge (`merge`, `squash`, `rebase`) y revisiones (con aclaración de estado `PENDING` al omitir `event`).
3. **Pipeline de RAG y Agente Implementado en `TP2_Laboratorio_RAG_Agente.ipynb` y `agente_cli.py`:**
   * **Limpieza:** Normalización de saltos de línea, eliminación de separadores `---`, marcas de negrita `**` y líneas vacías repetidas (`limpiar_markdown`).
   * **Chunking estructural en 2 etapas:** `MarkdownHeaderTextSplitter` (corta por `#`, `##`, `###` para mantener 1 endpoint completo por chunk) + `RecursiveCharacterTextSplitter` (`chunk_size=1500`, `chunk_overlap=150`) como resguardo, anteponiendo la ruta jerárquica de encabezados (`[Documento > Sección > Subsección]`) a cada fragmento (39 chunks en total).
   * **Embeddings Multilingües:** `intfloat/multilingual-e5-small` (384 dimensiones, normalizados, con prefijos `query: ` y `passage: `).
   * **Vector Store y Búsqueda Híbrida:** `FAISS` (`IndexFlatIP`, similitud coseno exacta) combinado con ranking léxico **Okapi BM25** (`IndiceBM25`), fusionados mediante **Reciprocal Rank Fusion (RRF)** ($k_{RRF}=60$, top-4 fragmentos).
   * **Evaluación Cuantitativa del Recuperador:** Benchmark sobre 16 consultas parafraseadas comparando `all-MiniLM-L6-v2` (Hit@1: 0.38, MRR: 0.48), `multilingual-e5-small` (Hit@1: 0.69, MRR: 0.78), `BM25` (Hit@1: 0.75, MRR: 0.83) e **Híbrida e5 + BM25 RRF** (Hit@1: 0.88, Hit@4: 0.94, MRR: 0.89).
   * **LLM Local:** `ChatOllama` conectado a Ollama local (`http://localhost:11434`) usando `qwen2.5:7b` (`temperature=0`, `num_ctx=8192`).
   * **Agente y Tools:** Orquestado con `create_agent` (ciclo ReAct con tool calling) y 3 herramientas (`consultar_documentacion_github`, `consultar_repositorio_github` con separación de issues y PRs vía `/search/issues`, y `calcular_cuota_rate_limit`).

---

## 3. Estado Actual de las Fases

* [x] **Fase 1:** Organización.
* [x] **Fase 2:** Selección del Dominio Técnico.
* [x] **Fase 2:** Creación y Limpieza del Corpus Técnico.
* [x] **Fase 2:** Segmentación (*Chunking*), Embeddings e Indexación con FAISS + BM25 (RRF).
* [x] **Fase 2:** Motor de Recuperación (*Retrieval*) y Evaluación Cuantitativa (Hit@1, Hit@4, MRR).
* [x] **Fase 3 - Parte 1:** Conexión e Integración (Vincular Retriever con el LLM mediante LCEL).
* [x] **Fase 3 - Parte 2:** **Lógica de Agente y Herramientas (*Tools*) [COMPLETADA]**.
* [x] **Entregables:** **Notebook Ejecutado + Informe Técnico de 2 páginas (`Informe_Tecnico_TP2.pdf` y `.docx`) [COMPLETADOS]**.

---

## 5. Configuración de Git y Credenciales
* **Host SSH personal:** `github-personal` (configurado en `~/.ssh/config` para usar la llave `~/.ssh/id_ed25519_personal` vinculada a la cuenta GitHub `Facu-devel-2004`).
* **Remote Git:** `git@github-personal:Facu-devel-2004/IA_TP2.git` (mapeado a `https://github.com/Facu-devel-2004/IA_TP2`).
