#!/usr/bin/env python3
"""
Agente Interactivo de Consola (CLI) - Trabajo de Laboratorio N° 2
Inteligencia Artificial - Sistemas Inteligentes (FCEFyN)

Conecta el LLM local 'qwen2.5:1.5b' (Ollama) con:
1. RAG sobre la especificación técnica de la API REST de GitHub (FAISS + sentence-transformers).
2. Herramienta externa en vivo para consultar métricas reales de repositorios en GitHub.
3. Herramienta analítica de evaluación de Rate Limit.
"""

import os
import sys
import glob
import json
import requests
from typing import List, Any

# LangChain y componentes de RAG y Agentes
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage, AIMessage
from langchain_openai import ChatOpenAI

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "corpus")
FAISS_INDEX_DIR = os.path.join(os.path.dirname(__file__), "faiss_github_api_index")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
MODEL_NAME = "qwen2.5:1.5b"


def inicializar_vectorstore():
    """Carga el índice FAISS desde disco o lo construye a partir del corpus si no existe."""
    print("⏳ Inicializando modelo de embeddings...")
    embedding_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    if os.path.exists(FAISS_INDEX_DIR):
        print(f"📦 Cargando índice FAISS existente desde '{FAISS_INDEX_DIR}'...")
        try:
            vectorstore = FAISS.load_local(
                FAISS_INDEX_DIR,
                embedding_model,
                allow_dangerous_deserialization=True
            )
            return vectorstore
        except Exception as e:
            print(f"⚠️ Error al cargar índice local: {e}. Reconstruyendo...")

    print("📄 Procesando documentos del corpus en './corpus'...")
    md_files = sorted(glob.glob(os.path.join(CORPUS_DIR, "*.md")))
    tech_files = [f for f in md_files if not os.path.basename(f).lower().startswith("readme")]

    raw_docs = []
    for fp in tech_files:
        loader = TextLoader(fp, encoding="utf-8")
        raw_docs.extend(loader.load())

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=120,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    chunks = text_splitter.split_documents(raw_docs)
    print(f"✂️ Chunks generados: {len(chunks)}. Indexando en FAISS...")

    vectorstore = FAISS.from_documents(documents=chunks, embedding=embedding_model)
    vectorstore.save_local(FAISS_INDEX_DIR)
    print("✅ Índice FAISS guardado en disco exitosamente.")
    return vectorstore


def formatear_contexto(docs: List[Any]) -> str:
    """Formatea los fragmentos recuperados para trazabilidad del RAG."""
    bloques = []
    for i, doc in enumerate(docs, 1):
        fuente = os.path.basename(doc.metadata.get("source", "desconocido"))
        bloques.append(f"--- [FRAGMENTO {i} | FUENTE: {fuente}] ---\n{doc.page_content.strip()}")
    return "\n\n".join(bloques)


def construir_agente():
    """Configura las herramientas, el LLM de Ollama y el agente ReAct."""
    vectorstore = inicializar_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

    # 1. Definición de Herramientas
    @tool
    def consultar_documentacion_github(consulta: str) -> str:
        """
        Consulta la documentación técnica oficial de la API REST de GitHub (v3).
        Útil para conocer: endpoints, métodos HTTP (GET, POST, PATCH), parámetros,
        cabeceras (headers), códigos de estado y reglas de rate limit teórico.
        """
        docs = retriever.invoke(consulta)
        if not docs:
            return "No se encontraron fragmentos relevantes en la documentación técnica del corpus."
        return formatear_contexto(docs)

    @tool
    def consultar_repositorio_github(owner: str, repo: str) -> str:
        """
        Consulta información y métricas EN VIVO de un repositorio público en GitHub
        mediante una llamada real a la API REST de GitHub.
        Input:
          - owner: dueño o empresa (ej: 'facebook', 'reflex-dev', 'octocat').
          - repo: nombre del repo (ej: 'react', 'reflex', 'Hello-World').
        Devuelve estrellas actuales, forks, issues abiertos, lenguaje y descripción.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {
            "User-Agent": "Laboratorio-IA-TP2-Agent-CLI/1.0",
            "Accept": "application/vnd.github+json"
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                resultado = {
                    "repositorio": data.get("full_name"),
                    "descripcion": data.get("description", "Sin descripción"),
                    "estrellas": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "issues_abiertos": data.get("open_issues_count", 0),
                    "lenguaje_principal": data.get("language", "No especificado"),
                    "ultima_actualizacion": data.get("updated_at", ""),
                    "url_html": data.get("html_url", "")
                }
                return json.dumps(resultado, indent=2, ensure_ascii=False)
            elif response.status_code == 404:
                return f"Error 404: El repositorio '{owner}/{repo}' no existe en GitHub."
            elif response.status_code == 403:
                return "Error 403: Límite de solicitudes de la API pública alcanzado."
            else:
                return f"Error HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return f"Error de conexión con GitHub: {str(e)}"

    @tool
    def calcular_cuota_rate_limit(solicitudes_por_hora: int, es_autenticado: bool = False) -> str:
        """
        Calcula y evalúa el estado del Rate Limit según las reglas oficiales de GitHub.
        Devuelve el límite permitido, solicitudes restantes y porcentaje consumido.
        """
        limite = 5000 if es_autenticado else 60
        restante = max(0, limite - solicitudes_por_hora)
        porcentaje = min(100.0, (solicitudes_por_hora / limite) * 100)
        estado = "DENTRO DEL LÍMITE" if solicitudes_por_hora <= limite else "EXCEDIDO (Error 403)"

        return json.dumps({
            "tipo_usuario": "Autenticado (PAT/OAuth)" if es_autenticado else "No Autenticado (Anónimo)",
            "limite_por_hora": limite,
            "solicitudes_planificadas": solicitudes_por_hora,
            "solicitudes_restantes": restante,
            "porcentaje_consumido": f"{porcentaje:.1f}%",
            "estado": estado
        }, indent=2, ensure_ascii=False)

    tools = [
        consultar_documentacion_github,
        consultar_repositorio_github,
        calcular_cuota_rate_limit
    ]

    # 2. Conexión con Ollama local (temperatura 0 para máxima precisión de Tool Calling)
    print(f"🤖 Conectando con Ollama local ({MODEL_NAME} en {OLLAMA_BASE_URL})...")
    llm = ChatOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
        model=MODEL_NAME,
        temperature=0.0
    )

    # Prompt del sistema optimizado para modelos compactos: fuerza Tool Calling directo sin cháchara
    system_prompt_agente = (
        "You are a technical GitHub assistant with access to tools.\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Whenever the user mentions a repository or asks for stars, forks, issues, description or repository stats, "
        "you MUST NOT explain what you are going to do. You MUST directly call `consultar_repositorio_github` immediately.\n"
        "2. Whenever the user asks about GitHub API documentation, endpoints, headers, or rules, "
        "you MUST call `consultar_documentacion_github` immediately.\n"
        "3. When the user asks for both documentation and repository stats, call both tools and synthesize.\n"
        "4. Always formulate the final answer to the user in Spanish, clearly and professionally."
    )

    # 3. Orquestador
    try:
        from langchain.agents import create_agent
        agent_executor = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt_agente
        )
        modo = "create_agent (LangGraph)"
    except (ImportError, Exception):
        from langchain.agents import create_tool_calling_agent, AgentExecutor
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

        prompt_agente = ChatPromptTemplate.from_messages([
            ("system", system_prompt_agente),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad", optional=True)
        ])
        agent = create_tool_calling_agent(llm, tools, prompt_agente)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        modo = "create_tool_calling_agent + AgentExecutor"

    print(f"✅ Agente listo y operativo ({modo}).\n")
    return agent_executor, modo


def main():
    print("=" * 80)
    print("🤖 AGENTE INTELIGENTE DE GITHUB - TERMINAL INTERACTIVA (TP2)")
    print("   Modelo Local: qwen2.5:1.5b (Ollama) | RAG: FAISS | Tools: GitHub REST API")
    print("=" * 80)
    print("Escribí tu consulta en lenguaje natural. Ejemplos:")
    print("  • '¿Cuántas estrellas e issues tiene reflex-dev/reflex?'")
    print("  • '¿Cuáles son las cabeceras obligatorias según la documentación?'")
    print("  • '¿Cómo crear un issue según la doc y cuántos issues tiene facebook/react?'")
    print("Para salir, escribí 'salir' o 'exit'.\n")

    try:
        agent_executor, modo = construir_agente()
    except Exception as e:
        print(f"\n❌ Error al inicializar el agente: {e}")
        print("Asegurate de tener Ollama corriendo ('ollama serve') y el modelo descargado ('ollama pull qwen2.5:1.5b').")
        sys.exit(1)

    while True:
        try:
            pregunta = input("\n🧑‍💻 Vos > ").strip()
            if not pregunta:
                continue
            if pregunta.lower() in ["salir", "exit", "quit", "q"]:
                print("👋 ¡Hasta luego!")
                break

            print("\n⏳ El agente está procesando tu consulta con sus herramientas...")
            if modo.startswith("create_agent"):
                salida = agent_executor.invoke({"messages": [{"role": "user", "content": pregunta}]})
                
                # Visualizar pasos intermedios de herramientas
                for m in salida.get("messages", []):
                    if isinstance(m, AIMessage) and m.tool_calls:
                        for tc in m.tool_calls:
                            print(f"  ⚙️ [Herramienta]: {tc['name']}({tc.get('args', {})})")
                    elif isinstance(m, ToolMessage):
                        print(f"  📥 [Resultado recibido de {m.name}]: {m.content[:180]}...")
                
                respuesta = salida["messages"][-1].content
            else:
                salida = agent_executor.invoke({"input": pregunta})
                respuesta = salida.get("output", str(salida))

            print(f"\n🤖 Agente >\n{respuesta}")
            print("-" * 80)

        except KeyboardInterrupt:
            print("\n👋 Sesión interrumpida. ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error al procesar consulta: {e}")


if __name__ == "__main__":
    main()
