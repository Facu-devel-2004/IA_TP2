#!/usr/bin/env python3
"""
Agente RAG de consola — Trabajo de Laboratorio N° 2 (IA – Sistemas Inteligentes, FCEFyN).

Versión interactiva del pipeline del notebook TP2_Laboratorio_RAG_Agente.ipynb:
  1. Limpia y segmenta el corpus de la API REST de GitHub (./corpus).
  2. Indexa los fragmentos con embeddings multilingües (intfloat/multilingual-e5-small) en FAISS y
     con BM25; la búsqueda combina ambos rankings con Reciprocal Rank Fusion.
  3. Conecta un LLM local servido por Ollama (qwen2.5:7b por defecto) como agente ReAct con tres
     herramientas: búsqueda en la documentación (RAG), consulta en vivo a la API de GitHub y
     cálculo de cuota de rate limit.

Uso:
    python agente_cli.py                      # modo interactivo
    python agente_cli.py "¿pregunta?"         # responde una sola pregunta y termina

Variables de entorno opcionales:
    OLLAMA_MODEL     modelo de Ollama (por defecto qwen2.5:7b)
    OLLAMA_BASE_URL  URL del servidor de Ollama (por defecto http://localhost:11434)
    GITHUB_TOKEN     token de GitHub para tener una cuota de 5000 solicitudes/hora
"""

import json
import math
import os
import re
import sys
import time
import unicodedata
import warnings
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests
from sentence_transformers import SentenceTransformer

warnings.filterwarnings("ignore", category=DeprecationWarning)  # avisos de deprecación de langchain-community

from langchain.agents import create_agent
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# Configuración (mismos valores que el notebook)
# ---------------------------------------------------------------------------
CORPUS_DIR = Path(__file__).resolve().parent / "corpus"
MODELO_EMBEDDINGS = "intfloat/multilingual-e5-small"
CHUNK_SIZE = 1500     # una sección (endpoint) por fragmento
CHUNK_OVERLAP = 150
TOP_K = 4          # fragmentos que recibe el LLM
CANDIDATOS = 10    # candidatos de cada buscador antes de fusionar
RRF_K = 60         # constante de Reciprocal Rank Fusion
MODELO_LLM = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
CONTEXTO_LLM = 8192
GITHUB_API = "https://api.github.com"

PROMPT_SISTEMA = """Eres un asistente técnico experto en la API REST de GitHub. Dispones de tres herramientas:
- consultar_documentacion_github: busca en la documentación técnica del corpus (endpoints, métodos HTTP, parámetros, cabeceras, códigos de estado, autenticación y límites de uso).
- consultar_repositorio_github: obtiene datos EN VIVO de un repositorio público concreto (estrellas, forks, issues y pull requests abiertos, lenguaje).
- calcular_cuota_rate_limit: calcula el consumo de la cuota horaria para una cantidad de solicitudes por hora.

Cómo trabajar:
1. Identifica todas las partes de la pregunta y llama a TODAS las herramientas necesarias antes de responder. Si la pregunta de documentación abarca varios temas, haz una búsqueda por tema.
2. Si la pregunta menciona endpoints, métodos HTTP, parámetros o campos, cabeceras, códigos de estado o de error, autenticación o límites, DEBES llamar a consultar_documentacion_github, aunque también uses otras herramientas. Nunca respondas esos datos de memoria.
3. Si el usuario nombra un repositorio (por ejemplo facebook/react) y pide datos actuales, usa consultar_repositorio_github.
4. Si el usuario menciona una cantidad de solicitudes por hora, usa calcular_cuota_rate_limit una vez por cada escenario e informa el límite que corresponde y el porcentaje consumido.

Reglas para la respuesta final:
- Escribe en español, de forma breve y ordenada, respondiendo cada parte de la pregunta en el mismo orden.
- Usa EXCLUSIVAMENTE la información devuelta por las herramientas; nunca la completes con conocimiento propio.
- Sé completo: si los fragmentos enumeran varios elementos (cabeceras, campos, códigos, opciones), menciónalos todos, y distingue claramente los campos obligatorios de los opcionales.
- Si los fragmentos de la documentación no mencionan lo que se pregunta (por ejemplo, un endpoint que no aparece en ellos), responde que la documentación del corpus no contiene esa información.
- Agrega [Fuente: archivo.md] después de cada dato tomado de la documentación. Presenta los resultados de calcular_cuota_rate_limit como un cálculo y los de consultar_repositorio_github como datos obtenidos en vivo de la API de GitHub."""


# ---------------------------------------------------------------------------
# Fase 2: corpus, segmentación, embeddings e indexación
# ---------------------------------------------------------------------------
def limpiar_markdown(texto: str) -> str:
    """Normaliza el texto de un documento antes de segmentarlo."""
    texto = texto.replace("\r\n", "\n")
    texto = re.sub(r"^\s*---\s*$", "", texto, flags=re.MULTILINE)  # separadores horizontales
    texto = texto.replace("**", "")                                 # negritas
    texto = re.sub(r"[ \t]+$", "", texto, flags=re.MULTILINE)       # espacios al final de línea
    texto = re.sub(r"\n{3,}", "\n\n", texto)                         # líneas vacías repetidas
    return texto.strip()


def segmentar_corpus(directorio: Path) -> list:
    """Divide cada documento por encabezados Markdown y luego por tamaño, anteponiendo la ruta de encabezados."""
    divisor_markdown = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "documento"), ("##", "seccion"), ("###", "subseccion")],
        strip_headers=True,
    )
    divisor_recursivo = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, separators=["\n\n", "\n* ", "\n", " "]
    )
    chunks = []
    for ruta in sorted(directorio.glob("*.md")):
        if ruta.name.lower().startswith("readme"):
            continue
        secciones = divisor_markdown.split_text(limpiar_markdown(ruta.read_text(encoding="utf-8")))
        for seccion in secciones:
            seccion.metadata["source"] = ruta.name
        for fragmento in divisor_recursivo.split_documents(secciones):
            m = fragmento.metadata
            m["id"] = len(chunks)
            m["ruta"] = " > ".join(m[k] for k in ("documento", "seccion", "subseccion") if k in m)
            fragmento.page_content = f"[{m['ruta']}]\n{fragmento.page_content}"
            chunks.append(fragmento)
    return chunks


class EmbeddingsSentenceTransformers(Embeddings):
    """Adaptador entre sentence-transformers y LangChain (con los prefijos que requieren los modelos E5)."""

    def __init__(self, nombre_modelo: str, prefijo_consulta: str = "", prefijo_documento: str = ""):
        self.modelo = SentenceTransformer(nombre_modelo)
        self.prefijo_consulta = prefijo_consulta
        self.prefijo_documento = prefijo_documento

    def embed_documents(self, textos: list) -> list:
        textos = [self.prefijo_documento + t for t in textos]
        return self.modelo.encode(textos, normalize_embeddings=True, batch_size=16).tolist()

    def embed_query(self, texto: str) -> list:
        return self.modelo.encode(self.prefijo_consulta + texto, normalize_embeddings=True).tolist()


def formatear_contexto(documentos) -> str:
    """Une los fragmentos recuperados indicando su archivo de origen."""
    return "\n\n".join(
        f"--- FRAGMENTO {i} | FUENTE: {doc.metadata['source']} ---\n{doc.page_content}"
        for i, doc in enumerate(documentos, 1)
    )


STOPWORDS = set(
    "a al algo como con cual cuales cuando de del el ella en entre es esta este esto hay la las lo los mas me mi "
    "mis muy no o para pero por que se si sin sobre su sus un una uno unos y ya yo tu te ti le les nos son ser "
    "fue era donde quiero puedo debo hace hacer cada otro otra".split()
)


def tokenizar(texto: str) -> list:
    """Minúsculas, sin tildes, sin stopwords y con un recorte simple de plurales."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    tokens = re.findall(r"[a-z0-9_]+", texto)
    return [t[:-1] if len(t) > 4 and t.endswith("s") else t for t in tokens if t not in STOPWORDS]


class IndiceBM25:
    """Implementación de Okapi BM25 sobre los fragmentos del corpus."""

    def __init__(self, documentos: list, k1: float = 1.5, b: float = 0.75):
        self.documentos = documentos
        self.tokens = [tokenizar(d.page_content) for d in documentos]
        self.frecuencias = [Counter(t) for t in self.tokens]
        self.k1, self.b = k1, b
        self.largo_medio = sum(map(len, self.tokens)) / len(self.tokens)
        n = len(documentos)
        df = Counter(t for toks in self.tokens for t in set(toks))
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def buscar(self, consulta: str, k: int) -> list:
        terminos = tokenizar(consulta)
        puntajes = []
        for frec, toks in zip(self.frecuencias, self.tokens):
            norma = self.k1 * (1 - self.b + self.b * len(toks) / self.largo_medio)
            puntajes.append(sum(self.idf[t] * frec[t] * (self.k1 + 1) / (frec[t] + norma) for t in terminos if t in frec))
        orden = sorted(range(len(puntajes)), key=lambda i: puntajes[i], reverse=True)[:k]
        return [self.documentos[i] for i in orden if puntajes[i] > 0]


class RecuperadorHibrido:
    """Búsqueda semántica (FAISS) + léxica (BM25) fusionadas con Reciprocal Rank Fusion."""

    def __init__(self, vectorstore, indice_bm25):
        self.vectorstore = vectorstore
        self.indice_bm25 = indice_bm25

    def __call__(self, consulta: str, k: int = TOP_K) -> list:
        listas = [self.vectorstore.similarity_search(consulta, k=CANDIDATOS),
                  self.indice_bm25.buscar(consulta, k=CANDIDATOS)]
        puntaje, documento = {}, {}
        for resultados in listas:
            for rango, doc in enumerate(resultados, 1):
                clave = doc.metadata["id"]
                puntaje[clave] = puntaje.get(clave, 0.0) + 1 / (RRF_K + rango)
                documento[clave] = doc
        return [documento[c] for c in sorted(puntaje, key=puntaje.get, reverse=True)[:k]]


# ---------------------------------------------------------------------------
# Fase 3: herramientas del agente
# ---------------------------------------------------------------------------
def cabeceras_github() -> dict:
    """Cabeceras recomendadas en 01_autenticacion_y_rate_limits.md."""
    cabeceras = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "IA-TP2-Agente-RAG",
    }
    if os.environ.get("GITHUB_TOKEN"):
        cabeceras["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    return cabeceras


def contar_resultados_busqueda(consulta: str):
    """Devuelve total_count de GET /search/issues, o None si la búsqueda falla."""
    try:
        r = requests.get(f"{GITHUB_API}/search/issues", params={"q": consulta, "per_page": 1},
                         headers=cabeceras_github(), timeout=15)
        if r.status_code == 200:
            return r.json().get("total_count")
    except requests.RequestException:
        pass
    return None


def crear_herramientas(recuperar) -> list:
    """Define las tres herramientas; la de documentación usa la función de búsqueda recibida."""

    @tool
    def consultar_documentacion_github(consulta: str) -> str:
        """Busca en la documentación técnica de la API REST de GitHub y devuelve los fragmentos más
        relevantes con su archivo de origen. Úsala para preguntas sobre endpoints, métodos HTTP,
        parámetros, cabeceras, códigos de estado, autenticación o límites de uso (rate limit).

        Args:
            consulta: tema o pregunta técnica a buscar, en español (ej. "campos obligatorios para crear un issue").
        """
        documentos = recuperar(consulta)
        if not documentos:
            return "No se encontraron fragmentos relevantes en la documentación."
        return ("Fragmentos recuperados de la documentación. Usa sólo lo que dicen estos fragmentos; si no "
                "contienen la respuesta, indica que la documentación del corpus no incluye esa información.\n\n"
                + formatear_contexto(documentos))

    @tool
    def consultar_repositorio_github(owner: str, repo: str) -> str:
        """Consulta EN VIVO la API pública de GitHub y devuelve datos actuales de un repositorio:
        estrellas, forks, issues abiertos (sin contar pull requests), pull requests abiertos,
        lenguaje principal, descripción y fecha del último push.

        Args:
            owner: usuario u organización dueña del repositorio (ej. "facebook").
            repo: nombre del repositorio (ej. "react").
        """
        if "/" in owner:  # tolera entradas del tipo owner="facebook/react"
            owner, _, resto = owner.partition("/")
            repo = repo or resto
        owner, repo = owner.strip(), repo.strip()
        try:
            r = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=cabeceras_github(), timeout=15)
        except requests.RequestException as error:
            return f"Error de conexión con la API de GitHub: {error}"
        if r.status_code == 404:
            return f"Error 404: el repositorio '{owner}/{repo}' no existe o es privado."
        if r.status_code in (403, 429):
            return (f"Error {r.status_code}: se alcanzó el rate limit de la API de GitHub "
                    f"(x-ratelimit-remaining={r.headers.get('x-ratelimit-remaining')}). Reintentar más tarde.")
        if r.status_code != 200:
            return f"Error HTTP {r.status_code} al consultar la API de GitHub."

        datos = r.json()
        nombre = datos["full_name"]
        issues = contar_resultados_busqueda(f"repo:{nombre} is:issue is:open")
        pull_requests = contar_resultados_busqueda(f"repo:{nombre} is:pr is:open")
        resultado = {"fuente": "datos obtenidos en vivo de la API de GitHub", "repositorio": nombre}
        if nombre.lower() != f"{owner}/{repo}".lower():
            resultado["nota"] = f"GitHub redirigió '{owner}/{repo}' a '{nombre}' (el repositorio fue transferido o renombrado)."
        resultado.update({
            "descripcion": datos.get("description") or "Sin descripción",
            "lenguaje_principal": datos.get("language") or "No especificado",
            "estrellas": datos.get("stargazers_count"),
            "forks": datos.get("forks_count"),
        })
        if issues is not None and pull_requests is not None:
            resultado["issues_abiertos"] = issues
            resultado["pull_requests_abiertos"] = pull_requests
        else:  # la Search API falló: se informa el total combinado aclarando qué incluye
            resultado["issues_y_pull_requests_abiertos"] = datos.get("open_issues_count")
        resultado.update({
            "ultimo_push": datos.get("pushed_at"),
            "consultado": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M (hora local)"),
            "url": datos.get("html_url"),
        })
        return json.dumps(resultado, ensure_ascii=False, indent=2)

    @tool
    def calcular_cuota_rate_limit(solicitudes_por_hora: int, autenticado: bool = False) -> str:
        """Calcula el consumo de la cuota horaria de la API REST de GitHub (60 solicitudes por hora sin
        autenticar, 5000 con token) para una cantidad de solicitudes por hora. Devuelve el límite, las
        solicitudes restantes o excedentes, el porcentaje consumido y el intervalo mínimo entre solicitudes.

        Args:
            solicitudes_por_hora: cantidad de solicitudes que se planea hacer en una hora.
            autenticado: True si se usa un token (PAT, OAuth o GitHub App); False si son anónimas.
        """
        limite = 5000 if autenticado else 60
        tipo = "con token" if autenticado else "sin autenticar"
        porcentaje = 100 * solicitudes_por_hora / limite
        excedente = max(0, solicitudes_por_hora - limite)
        restantes = max(0, limite - solicitudes_por_hora)
        if excedente:
            resumen = (f"{solicitudes_por_hora} solicitudes por hora {tipo} SUPERAN el límite de {limite} por hora "
                       f"({porcentaje:.1f}% de la cuota, {excedente} solicitudes de exceso).")
        else:
            resumen = (f"{solicitudes_por_hora} solicitudes por hora {tipo} están DENTRO del límite de {limite} por hora "
                       f"({porcentaje:.1f}% de la cuota; quedan {restantes} disponibles).")
        return json.dumps({
            "resumen": resumen,
            "tipo_de_acceso": tipo,
            "limite_por_hora": limite,
            "solicitudes_planificadas": solicitudes_por_hora,
            "porcentaje_de_cuota": f"{porcentaje:.1f}%",
            "solicitudes_restantes": restantes,
            "solicitudes_excedentes": excedente,
            "intervalo_minimo_entre_solicitudes_seg": round(3600 / limite, 2),
        }, ensure_ascii=False, indent=2)

    return [consultar_documentacion_github, consultar_repositorio_github, calcular_cuota_rate_limit]


def construir_agente():
    """Construye el índice FAISS, las herramientas y el agente ReAct."""
    print("Segmentando el corpus...")
    chunks = segmentar_corpus(CORPUS_DIR)
    print(f"Calculando embeddings de {len(chunks)} fragmentos con {MODELO_EMBEDDINGS}...")
    embeddings = EmbeddingsSentenceTransformers(MODELO_EMBEDDINGS, "query: ", "passage: ")
    vectorstore = FAISS.from_documents(chunks, embeddings, distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT)
    recuperar = RecuperadorHibrido(vectorstore, IndiceBM25(chunks))

    print(f"Conectando con {MODELO_LLM} en {OLLAMA_URL}...")
    llm = ChatOllama(model=MODELO_LLM, base_url=OLLAMA_URL, temperature=0, num_ctx=CONTEXTO_LLM)
    llm.invoke("ok")  # falla temprano si Ollama no está disponible
    return create_agent(model=llm, tools=crear_herramientas(recuperar), system_prompt=PROMPT_SISTEMA)


def responder(agente, historial: list, pregunta: str) -> str:
    """Ejecuta el agente mostrando las acciones y observaciones del ciclo ReAct."""
    inicio = time.perf_counter()
    estado = agente.invoke({"messages": historial + [HumanMessage(pregunta)]}, config={"recursion_limit": 12})
    nuevos = estado["messages"][len(historial) + 1:]
    for mensaje in nuevos:
        if isinstance(mensaje, AIMessage) and mensaje.tool_calls:
            for llamada in mensaje.tool_calls:
                print(f"  [Acción]      {llamada['name']}({json.dumps(llamada['args'], ensure_ascii=False)})")
        elif isinstance(mensaje, ToolMessage):
            print(f"  [Observación] {mensaje.name}: {mensaje.content[:150].replace(chr(10), ' ')}...")
    respuesta = estado["messages"][-1].content
    print(f"\nAgente ({time.perf_counter() - inicio:.0f} s) >\n{respuesta}\n" + "-" * 80)
    return respuesta


def main() -> None:
    print("=" * 80)
    print("AGENTE RAG — API REST DE GITHUB (TP2, IA – Sistemas Inteligentes)")
    print("=" * 80)
    try:
        agente = construir_agente()
    except Exception as error:  # noqa: BLE001 - se informa cualquier fallo de inicialización
        print(f"\nNo se pudo iniciar el agente: {error}")
        print(f"Verifica que Ollama esté abierto y que el modelo esté descargado (ollama pull {MODELO_LLM}).")
        sys.exit(1)

    if len(sys.argv) > 1:  # modo de una sola pregunta
        responder(agente, [], " ".join(sys.argv[1:]))
        return

    print("\nEjemplos:")
    print("  - ¿Qué campos son obligatorios para crear un pull request?")
    print("  - ¿Cuántas estrellas e issues abiertos tiene facebook/react?")
    print("  - Si hago 100 solicitudes por hora sin token, ¿supero el límite?")
    print("Escribe 'nuevo' para borrar la conversación o 'salir' para terminar.\n")

    historial = []  # sólo preguntas y respuestas finales, para permitir repreguntas breves
    while True:
        try:
            pregunta = input("Tú > ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not pregunta:
            continue
        if pregunta.lower() in {"salir", "exit", "quit"}:
            break
        if pregunta.lower() == "nuevo":
            historial = []
            print("Conversación reiniciada.\n")
            continue
        try:
            respuesta = responder(agente, historial, pregunta)
            historial += [HumanMessage(pregunta), AIMessage(respuesta)]
        except Exception as error:  # noqa: BLE001 - el agente no debe cerrarse por un error puntual
            print(f"Error al procesar la consulta: {error}\n")
    print("Hasta luego.")


if __name__ == "__main__":
    main()
