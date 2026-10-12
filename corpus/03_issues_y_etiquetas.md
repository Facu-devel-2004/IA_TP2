# Especificación Técnica: GitHub REST API - Gestión de Issues y Etiquetas

## 1. Endpoints para Issues (Incidencias)

Los *Issues* permiten rastrear tareas, errores, mejoras y consultas en un repositorio. En la arquitectura interna de GitHub, los Pull Requests también se consideran un tipo especial de issue, por lo que listar issues puede incluir pull requests a menos que se filtren explícitamente.

---

### 1.1 Listar Issues de un Repositorio
* **Método y Ruta:** `GET /repos/{owner}/{repo}/issues`
* **Parámetros de consulta (Query Params):**
  * `state`: Filtro de estado. Valores: `open` (por defecto), `closed`, `all`.
  * `sort`: Campo de ordenamiento. Valores: `created`, `updated`, `comments` (por defecto `created`).
  * `direction`: Dirección del ordenamiento. Valores: `asc`, `desc` (por defecto `desc`).
  * `since`: Marca de tiempo en formato ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`) para devolver sólo issues modificados después de esa fecha.
  * `labels`: Cadena de nombres de etiquetas separadas por comas (ej. `bug,ui`).
  * `assignee`: Nombre de usuario asignado o `none` para issues sin asignar o `*` para cualquier asignado.
  * `creator`: Nombre de usuario que creó el issue.
  * `per_page`: Cantidad de registros por página (máximo 100, defecto 30).
  * `page`: Número de página.

* **Ejemplo de Respuesta JSON:**
```json
[
  {
    "id": 1058293,
    "number": 42,
    "title": "Error en el pipeline de RAG con ChromaDB",
    "user": {
      "login": "octocat",
      "id": 1
    },
    "labels": [
      {
        "id": 208045946,
        "name": "bug",
        "color": "f29513"
      }
    ],
    "state": "open",
    "locked": false,
    "assignee": {
      "login": "octocat"
    },
    "comments": 3,
    "created_at": "2026-03-10T14:20:00Z",
    "updated_at": "2026-03-11T09:15:00Z",
    "closed_at": null,
    "body": "Se observa un timeout al intentar conectar con la base vectorial local."
  }
]
```

---

### 1.2 Crear un Issue
* **Método y Ruta:** `POST /repos/{owner}/{repo}/issues`
* **Código de respuesta exitosa:** `201 Created`
* **Cuerpo de la Solicitud (JSON Payload):**
  ```json
  {
    "title": "Falla de autenticación en endpoint /user/repos",
    "body": "Al enviar un token expirado, el mensaje devuelto debe ser 401 en lugar de 403.",
    "assignees": ["octocat"],
    "milestone": 1,
    "labels": ["bug", "backend", "prioridad-alta"]
  }
  ```
* **Parámetros Requeridos:**
  * `title` (string): Título breve y descriptivo del issue.
* **Parámetros Opcionales:**
  * `body` (string): Descripción detallada en formato Markdown.
  * `assignees` (array de strings): Nombres de usuario de GitHub para asignar la tarea.
  * `milestone` (integer): Número identificador del hito de entrega.
  * `labels` (array de strings): Nombres de las etiquetas a asociar.

---

### 1.3 Obtener un Issue Específico
* **Método y Ruta:** `GET /repos/{owner}/{repo}/issues/{issue_number}`
* **Parámetros de ruta:**
  * `{issue_number}`: Número secuencial del issue dentro del repositorio (ej. `42`).

---

### 1.4 Modificar o Cerrar un Issue
* **Método y Ruta:** `PATCH /repos/{owner}/{repo}/issues/{issue_number}`
* **Cuerpo de la Solicitud (JSON):**
  ```json
  {
    "state": "closed",
    "state_reason": "completed",
    "title": "Falla de autenticación resuelta",
    "body": "Se corrigió la validación de tokens en el middleware."
  }
  ```
* **Valores válidos para `state`:** `open`, `closed`.
* **Valores válidos para `state_reason`:** `completed` (resuelto satisfactoriamente), `not_planned` (descartado/no aplicable), `reopened` (reabierto).

---

### 1.5 Comentarios en un Issue
* **Listar comentarios de un issue:**
  * **Método y Ruta:** `GET /repos/{owner}/{repo}/issues/{issue_number}/comments`
* **Crear un nuevo comentario:**
  * **Método y Ruta:** `POST /repos/{owner}/{repo}/issues/{issue_number}/comments`
  * **Cuerpo de la Solicitud:**
    ```json
    {
      "body": "El parche fue mergeado en la rama main. Listo para testing."
    }
    ```

---

## 2. Endpoints para Labels (Etiquetas)

Las etiquetas permiten categorizar issues y pull requests por tipo, severidad o área funcional.

### 2.1 Listar Etiquetas del Repositorio
* **Método y Ruta:** `GET /repos/{owner}/{repo}/labels`

### 2.2 Crear una Nueva Etiqueta
* **Método y Ruta:** `POST /repos/{owner}/{repo}/labels`
* **Código de respuesta:** `201 Created`
* **Cuerpo de la Solicitud:**
  ```json
  {
    "name": "prioridad-alta",
    "description": "Indica tareas que deben resolverse en el sprint actual",
    "color": "d73a4a"
  }
  ```
  *(Nota: El color se especifica en formato hexadecimal de 6 caracteres sin el símbolo `#`).*

### 2.3 Asignar Etiquetas a un Issue Existente
* **Método y Ruta:** `POST /repos/{owner}/{repo}/issues/{issue_number}/labels`
* **Cuerpo de la Solicitud:**
  ```json
  {
    "labels": ["bug", "prioridad-alta"]
  }
  ```
