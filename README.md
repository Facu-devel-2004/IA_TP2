# Trabajo de Laboratorio N° 2 - Sistemas Inteligentes (IA)
## NLP – Representaciones Vectoriales – LLMs – RAG y Agentes

* **Cátedra:** Inteligencia Artificial – Sistemas Inteligentes (FCEFyN)
* **Dominio Técnico Seleccionado:** GitHub REST API (Especificación v3 / Versión 2022-11-28)
* **Repositorio:** [Facu-devel-2004/IA_TP2](https://github.com/Facu-devel-2004/IA_TP2)

---

## 📁 Estructura del Repositorio

```text
IA_TP2/
├── Trabajo de laboratorio 2 - Consignas.pdf   # Consignas oficiales del laboratorio
├── CONTEXTO_AGENTE_IA.md                     # Bitácora y contexto técnico para continuar el trabajo
├── README.md                                 # Documentación general del repositorio
├── TP2_Laboratorio_RAG_Agente.ipynb          # Notebook con el pipeline de RAG y Agente
└── corpus/                                   # Base de conocimientos técnica
    ├── README.md                             # Descripción y justificación del corpus
    ├── 01_autenticacion_y_rate_limits.md     # Auth, headers requeridos, cuotas y errores HTTP
    ├── 02_repositorios_y_ramas.md            # Endpoints de repositorios, branches y releases
    ├── 03_issues_y_etiquetas.md              # Endpoints de issues, comentarios y labels
    └── 04_pull_requests_y_revisiones.md      # Endpoints de PRs, merges y code reviews
```

---

## 🚀 Estado de Avance del Proyecto

| Fase | Actividad | Estado | Detalle |
| :--- | :--- | :---: | :--- |
| **Fase 1** | Organización Colaborativa | ✅ Completado | Selección de roles y entorno. |
| **Fase 2** | Dominio Técnico y Corpus | ✅ Completado | Delimitación formal sobre GitHub REST API con 4 documentos técnicos estructurados. |
| **Fase 2** | Chunking, Embeddings e Indexación | ✅ Completado | `RecursiveCharacterTextSplitter`, embeddings `all-MiniLM-L6-v2` y almacenamiento en FAISS. |
| **Fase 2** | Motor de Recuperación (Retrieval) | ✅ Completado | Validador de búsqueda semántica con consultas técnicas del dominio. |
| **Fase 3** | Conexión e Integración (RAG + LLM) | ✅ Completado | Integración mediante LCEL con `Qwen2.5-7B` (Hugging Face Router / ChatOpenAI) con prompts anti-alucinación y citas de fuente. |
| **Fase 3** | Lógica de Agente y Herramientas (*Tools*) | ⏳ Próximo paso | Implementación de tool de consulta en vivo / cálculo y orquestación con agente ReAct. |
| **Entregables**| Informe Técnico (Máx. 2 páginas) | ⏳ Próximo paso | Redacción del reporte técnico con metodología y ejemplos de interacción. |

---

## 🛠️ Requisitos e Instalación

Para ejecutar el notebook en local o en Google Colab:

```bash
pip install -q langchain langchain-community langchain-openai langchain-text-splitters faiss-cpu sentence-transformers requests
```

Para autenticar con el proveedor LLM (Hugging Face Router):
```python
import os
os.environ["HF_TOKEN"] = "tu_token_de_huggingface"
```
