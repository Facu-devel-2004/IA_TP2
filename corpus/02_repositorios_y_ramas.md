# Especificación Técnica: GitHub REST API - Gestión de Repositorios y Ramas

## 1. Endpoints para Repositorios

### 1.1 Listar Repositorios
* **Listar repositorios del usuario autenticado:**
  * **Método y Ruta:** `GET /user/repos`
  * **Parámetros de consulta (Query Params):**
    * `visibility`: `all`, `public`, `private` (por defecto `all`).
    * `affiliation`: `owner`, `collaborator`, `organization_member`.
    * `sort`: `created`, `updated`, `pushed`, `full_name` (por defecto `full_name`).
    * `per_page`: Entero de 1 a 100 (por defecto 30).
    * `page`: Número de página para paginación.

* **Listar repositorios públicos de un usuario específico:**
  * **Método y Ruta:** `GET /users/{username}/repos`
  * **No requiere autenticación** para usuarios públicos.

* **Listar repositorios de una organización:**
  * **Método y Ruta:** `GET /orgs/{org}/repos`

---

### 1.2 Obtener Información Detallada de un Repositorio
* **Método y Ruta:** `GET /repos/{owner}/{repo}`
* **Parámetros de ruta:**
  * `{owner}`: Nombre de usuario u organización dueña del repositorio.
  * `{repo}`: Nombre del repositorio.
* **Propiedades clave devueltas en la respuesta JSON:**
  * `id`: Identificador numérico único del repositorio.
  * `name`: Nombre simple del repositorio.
  * `full_name`: Nombre calificado completo (ej. `octocat/Hello-World`).
  * `private`: Booleano que indica si el repositorio es privado.
  * `description`: Texto descriptivo del proyecto.
  * `default_branch`: Rama principal por defecto (ej. `main` o `master`).
  * `stargazers_count`: Número total de estrellas otorgadas.
  * `forks_count`: Número de bifurcaciones.
  * `open_issues_count`: Número de issues abiertos (incluye pull requests abiertos).
  * `visibility`: String (`public`, `private`, `internal`).
  * `clone_url`: URL HTTPS para clonado Git.

---

### 1.3 Crear un Repositorio
* **Crear en la cuenta del usuario autenticado:**
  * **Método y Ruta:** `POST /user/repos`
  * **Código de respuesta exitosa:** `201 Created`
  * **Cuerpo de la Solicitud (JSON Payload):**
    ```json
    {
      "name": "nuevo-proyecto-ia",
      "description": "Repositorio creado mediante la API REST de GitHub",
      "private": false,
      "has_issues": true,
      "has_projects": true,
      "has_wiki": false,
      "auto_init": true,
      "gitignore_template": "Python",
      "license_template": "mit"
    }
    ```
  * **Parámetros Requeridos:**
    * `name` (string): Nombre del repositorio.
  * **Parámetros Opcionales Clave:**
    * `private` (boolean): `true` para repositorio privado, `false` para público.
    * `auto_init` (boolean): `true` para inicializar automáticamente con un archivo `README.md`.
    * `gitignore_template` (string): Nombre de la plantilla de `.gitignore` (ej. `Python`, `Node`).
    * `license_template` (string): Licencia open-source (ej. `mit`, `apache-2.0`, `gpl-3.0`).

* **Crear en una Organización:**
  * **Método y Ruta:** `POST /orgs/{org}/repos`

---

### 1.4 Modificar y Eliminar Repositorios
* **Actualizar configuración de un repositorio:**
  * **Método y Ruta:** `PATCH /repos/{owner}/{repo}`
  * Permite modificar `name`, `description`, `private`, `default_branch`, `archived` (`true` para archivar).
* **Eliminar un repositorio:**
  * **Método y Ruta:** `DELETE /repos/{owner}/{repo}`
  * **Código de respuesta:** `204 No Content`
  * Requiere token con scope `delete_repo` y permisos de administrador.

---

## 2. Endpoints para Ramas (Branches)

### 2.1 Listar Ramas de un Repositorio
* **Método y Ruta:** `GET /repos/{owner}/{repo}/branches`
* **Parámetros de consulta:**
  * `protected`: Filtra por estado de protección (`true` o `false`).
  * `per_page`: Número de resultados por página (máximo 100).
* **Estructura devuelta:**
  ```json
  [
    {
      "name": "main",
      "commit": {
        "sha": "7fd1a60b01f91b314f59955a4e4d4e80d8dee119",
        "url": "https://api.github.com/repos/owner/repo/commits/7fd1a60..."
      },
      "protected": true
    }
  ]
  ```

### 2.2 Obtener una Rama Específica
* **Método y Ruta:** `GET /repos/{owner}/{repo}/branches/{branch}`
* Devuelve detalles del último commit, autor, árbol y reglas de protección activa de la rama.

---

## 3. Endpoints para Releases (Lanzamientos de Versiones)

### 3.1 Listar Releases
* **Método y Ruta:** `GET /repos/{owner}/{repo}/releases`

### 3.2 Crear un Release
* **Método y Ruta:** `POST /repos/{owner}/{repo}/releases`
* **Cuerpo de la Solicitud (JSON):**
  ```json
  {
    "tag_name": "v1.0.0",
    "target_commitish": "main",
    "name": "Versión 1.0.0 Oficial",
    "body": "Notas de la versión con las nuevas características de IA.",
    "draft": false,
    "prerelease": false,
    "generate_release_notes": true
  }
  ```
