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
   * `01_autenticacion_y_rate_limits.md`: Base URL, headers requeridos (`User-Agent`, `Authorization`, etc.), cuotas (60/5000 req/h) y códigos HTTP.
   * `02_repositorios_y_ramas.md`: Endpoints de creación, listado, configuración de repositorios, branches y releases.
   * `03_issues_y_etiquetas.md`: Endpoints de issues, filtros (`state`, `sort`), creación, comentarios y labels.
   * `04_pull_requests_y_revisiones.md`: Endpoints de PRs, métodos de merge (`merge`, `squash`, `rebase`) y revisiones.
3. **Pipeline de RAG Implementado en `TP2_Laboratorio_RAG_Agente.ipynb`:**
   * **Carga:** `TextLoader` de LangChain.
   * **Chunking:** `RecursiveCharacterTextSplitter` con `chunk_size=600`, `chunk_overlap=120`, adaptado a encabezados de secciones Markdown.
   * **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` de Hugging Face.
   * **Vector Store:** `FAISS` con persistencia en disco (`save_local`).
   * **Retriever:** Búsqueda por similitud con $k=3$.
   * **LLM Local:** `ChatOpenAI` conectado a Ollama local (`http://localhost:11434/v1`) usando `qwen2.5:1.5b` (ligero, sin claves externas y con soporte nativo de tool calling).
   * **Conexión e Integración (LCEL):** Cadena `retriever | formatear_contexto` + `ChatPromptTemplate` con rol de especialista y regla anti-alucinación estricta + `llm` + `StrOutputParser()`.
   * **Agente y Tools:** Herramientas con `@tool` (`consultar_documentacion_github`, `consultar_repositorio_github`, `calcular_cuota_rate_limit`) orquestadas en runtime ReAct interactivo.

---

## 3. Estado Actual de las Fases

* [x] **Fase 1:** Organización.
* [x] **Fase 2:** Selección del Dominio Técnico.
* [x] **Fase 2:** Creación y Limpieza del Corpus Técnico.
* [x] **Fase 2:** Segmentación (*Chunking*), Embeddings e Indexación con FAISS.
* [x] **Fase 2:** Motor de Recuperación (*Retrieval*) y Validación Semántica.
* [x] **Fase 3 - Parte 1:** Conexión e Integración (Vincular Retriever con el LLM mediante LCEL).
* [x] **Fase 3 - Parte 2:** **Lógica de Agente y Herramientas (*Tools*) [COMPLETADA]**.
* [ ] **Entregables:** **Informe Técnico (máximo 2 páginas) [PENDIENTE]**.

---

## 4. Tareas Específicas para la Próxima Sesión

Cuando el usuario pida continuar, debes abordar inmediatamente:

### Tarea 1: Fase 3 - Lógica de Agente y Herramientas (*Tools*)
Configurar el LLM como un **Agente Interactivo (ReAct)** utilizando LangChain:
1. **Definir la Herramienta (*Tool*):**
   * Implementar con el decorador `@tool` de LangChain al menos una herramienta complementaria:
     * *Opción recomendada A:* `consultar_repositorio_github(owner, repo)`: consulta real vía `requests` a la API pública de GitHub para obtener metadatos en vivo (estrellas, forks, issues abiertos, descripción).
     * *Opción recomendada B:* `calcular_cuota_rate_limit(solicitudes_por_hora, es_autenticado)` o generador de comandos cURL validados.
2. **Definir la Herramienta de RAG (*Tool*):**
   * Envolver el retriever en una herramienta: `consultar_documentacion_github(query: str)`.
3. **Orquestar el Agente:**
   * Crear el agente con `create_agent` o `AgentExecutor` conectando el LLM con la lista `[consultar_documentacion_github, tool_adicional]`.
4. **Probar el Flujo Esperado de la Consigna:**
   * El usuario hace una consulta compleja (ej: *"¿Cómo se crea un issue según la documentación y cuántos issues abiertos tiene actualmente el repositorio facebook/react?"*).
   * El agente evalúa qué herramientas necesita, recupera fragmentos vía RAG, ejecuta la herramienta de consulta en vivo y genera una respuesta final integrada.

### Tarea 2: Elaboración del Informe Técnico (Entregable 2)
Redactar el informe de máximo 2 páginas que documente:
1. Metodología de construcción, limpieza y segmentación del corpus técnico.
2. Base vectorial elegida (FAISS) y técnica de búsqueda (similitud de cosenos).
3. Herramienta o acción adicional que implementa el agente y descripción de su flujo paso a paso.
4. Ejemplo real de interacción que muestre al menos 3 preguntas y sus respectivas respuestas correctas.

---

## 5. Configuración de Git y Credenciales
* **Host SSH personal:** `github-personal` (configurado en `~/.ssh/config` para usar la llave `~/.ssh/id_ed25519_personal` vinculada a la cuenta GitHub `Facu-devel-2004`).
* **Remote Git:** `git@github-personal:Facu-devel-2004/IA_TP2.git` (mapeado a `https://github.com/Facu-devel-2004/IA_TP2`).
