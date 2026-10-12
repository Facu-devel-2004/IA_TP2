# Corpus Técnico: GitHub REST API (Especificación v3 / 2022-11-28)

Este corpus reúne la especificación formal y acotada de la API REST oficial de GitHub para ser utilizado como base de conocimientos en el sistema **RAG (Retrieval-Augmented Generation)** del Trabajo de Laboratorio N° 2.

## Estructura de Documentos

1. [`01_autenticacion_y_rate_limits.md`](file:///home/FacuArch/Facultad/IA_Practica/IA_Ejercicios/IA_TP2/corpus/01_autenticacion_y_rate_limits.md):
   * URL base, cabeceras requeridas (`Accept`, `Authorization`, `X-GitHub-Api-Version`, `User-Agent`).
   * Mecanismos de autenticación (PAT clásicos vs Fine-grained, GitHub Apps).
   * Límites de tasa (*Rate Limiting*): Cuotas por hora (60 sin auth, 5000 con auth), endpoints de monitoreo (`/rate_limit`) y cabeceras de cuota.
   * Códigos de estado HTTP y diagnóstico de errores (200, 201, 204, 304, 401, 403, 404, 422).

2. [`02_repositorios_y_ramas.md`](file:///home/FacuArch/Facultad/IA_Practica/IA_Ejercicios/IA_TP2/corpus/02_repositorios_y_ramas.md):
   * Endpoints de repositorios: listar (`GET /user/repos`, `GET /users/{username}/repos`), detalles (`GET /repos/{owner}/{repo}`), crear (`POST /user/repos`), editar (`PATCH`), eliminar (`DELETE`).
   * Endpoints de ramas (*Branches*): listado de ramas y detalle de ramas protegidas.
   * Endpoints de versiones y lanzamientos (*Releases*): listado y creación.

3. [`03_issues_y_etiquetas.md`](file:///home/FacuArch/Facultad/IA_Practica/IA_Ejercicios/IA_TP2/corpus/03_issues_y_etiquetas.md):
   * Endpoints de incidencias (*Issues*): listado con filtros avanzados (`state`, `sort`, `since`, `labels`), creación con parámetros requeridos y opcionales, consulta, cierre (`PATCH`) y comentarios.
   * Endpoints de etiquetas (*Labels*): listado, creación con color hexadecimal y asignación a issues.

4. [`04_pull_requests_y_revisiones.md`](file:///home/FacuArch/Facultad/IA_Practica/IA_Ejercicios/IA_TP2/corpus/04_pull_requests_y_revisiones.md):
   * Endpoints de Pull Requests: listado por rama/estado, creación (`head`, `base`, `title`, `draft`), consulta de estado de integración (*mergeable*), fusión de ramas (`merge`, `squash`, `rebase`).
   * Endpoints de revisiones (*Reviews*): listado de revisiones y aprobación formal o solicitud de cambios (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`).

## Justificación para el Sistema RAG
* **Formalidad y precisión:** La documentación contiene parámetros técnicos estrictos y nombres exactos de campos JSON que los LLMs suelen alucinar si no cuentan con recuperación contextual.
* **Segmentación (*Chunking*):** Cada sección y subsección está estructurada con encabezados Markdown nivel 2 y 3 (`##`, `###`), lo que facilita un chunking semántico óptimo por endpoint y método HTTP.
* **Integración con Agentes:** Permite al agente no sólo explicar la API, sino invocar herramientas que interactúen con la API en vivo o generen comandos `curl` y scripts de automatización.
