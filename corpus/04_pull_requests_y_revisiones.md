# Especificación Técnica: GitHub REST API - Pull Requests y Revisiones de Código

## 1. Endpoints para Pull Requests

Los *Pull Requests* (PRs) permiten proponer cambios, revisar código y realizar la integración de ramas (*merging*) en un repositorio.

---

### 1.1 Listar Pull Requests
* **Método y Ruta:** `GET /repos/{owner}/{repo}/pulls`
* **Parámetros de consulta (Query Params):**
  * `state`: Estado del PR. Valores: `open` (por defecto), `closed`, `all`.
  * `head`: Filtra por rama origen en el formato `user:branch-name`.
  * `base`: Filtra por rama destino (ej. `main`).
  * `sort`: Campo de ordenamiento (`created`, `updated`, `popularity`, `long-running`). Por defecto `created`.
  * `direction`: `asc` o `desc` (por defecto `desc`).
  * `per_page`: Resultados por página (máximo 100, defecto 30).
  * `page`: Número de página.

---

### 1.2 Crear un Pull Request
* **Método y Ruta:** `POST /repos/{owner}/{repo}/pulls`
* **Código de respuesta exitosa:** `201 Created`
* **Cuerpo de la Solicitud (JSON Payload):**
  ```json
  {
    "title": "Implementación de ChromaDB en pipeline de RAG",
    "body": "Este PR introduce el motor de búsqueda vectorial usando ChromaDB y embeddings locales.",
    "head": "feature/chroma-rag",
    "base": "main",
    "draft": false,
    "maintainer_can_modify": true
  }
  ```
* **Parámetros Requeridos:**
  * `title` (string): Título descriptivo del Pull Request.
  * `head` (string): Nombre de la rama que contiene los cambios que se desean integrar. Si la rama proviene de un fork, debe tener el formato `nombre_usuario:rama`.
  * `base` (string): Nombre de la rama en la que se integrarán los cambios (ej. `main`).
* **Parámetros Opcionales:**
  * `body` (string): Descripción detallada del PR en Markdown.
  * `draft` (boolean): `true` para crear el PR en estado borrador (*draft*).
  * `maintainer_can_modify` (boolean): Permite que los mantenedores del repositorio base hagan commits en la rama origen.

---

### 1.3 Obtener un Pull Request Específico
* **Método y Ruta:** `GET /repos/{owner}/{repo}/pulls/{pull_number}`
* **Parámetros de ruta:**
  * `{pull_number}`: Número secuencial del PR.
* **Propiedades clave devueltas en la respuesta JSON:**
  * `id`: ID global único del PR.
  * `state`: Estado actual (`open`, `closed`).
  * `locked`: Booleano que indica si la conversación está bloqueada.
  * `merged`: Booleano que indica si los cambios ya fueron fusionados.
  * `mergeable`: Booleano o `null` que indica si se puede fusionar sin conflictos (si es `null`, GitHub aún está calculando el merge en segundo plano).
  * `mergeable_state`: Cadena que describe el estado de fusión (`clean`, `dirty`, `blocked`, `behind`, `unstable`).
  * `merged_at`: Timestamp de fusión o `null`.
  * `commits`: Cantidad de commits incluidos.
  * `additions`: Líneas de código agregadas.
  * `deletions`: Líneas de código eliminadas.
  * `changed_files`: Número total de archivos modificados.

---

### 1.4 Fusionar un Pull Request (Merge)
* **Método y Ruta:** `PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge`
* **Código de respuesta exitosa:** `200 OK`
* **Cuerpo de la Solicitud (JSON):**
  ```json
  {
    "commit_title": "Merge feature/chroma-rag into main (#12)",
    "commit_message": "Aprobado por el equipo de arquitectura de IA.",
    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "merge_method": "squash"
  }
  ```
* **Opciones para `merge_method`:**
  * `merge`: Crea un commit de fusión estándar preservando todos los commits individuales.
  * `squash`: Combina todos los commits del PR en un único commit en la rama base.
  * `rebase`: Aplica los commits de la rama origen secuencialmente sobre la rama base sin crear commit de merge.

---

## 2. Endpoints para Revisiones de Código (Pull Request Reviews)

Las revisiones permiten a los colaboradores auditar los cambios, dejar comentarios y aprobar o solicitar cambios antes del merge.

### 2.1 Listar Revisiones de un Pull Request
* **Método y Ruta:** `GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews`

### 2.2 Crear una Revisión
* **Método y Ruta:** `POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews`
* **Código de respuesta:** `200 OK`
* **Cuerpo de la Solicitud:**
  ```json
  {
    "commit_id": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "body": "Excelente trabajo. La implementación cumple con las consignas del laboratorio.",
    "event": "APPROVE"
  }
  ```
* **Valores válidos para el campo `event`:**
  * `APPROVE`: Aprueba formalmente el Pull Request para su fusión.
  * `REQUEST_CHANGES`: Solicita cambios indispensables antes de poder fusionar.
  * `COMMENT`: Deja un comentario general de revisión sin aprobar ni rechazar explícitamente.
  * `PENDING`: Deja la revisión en estado preliminar pendiente de publicación.
