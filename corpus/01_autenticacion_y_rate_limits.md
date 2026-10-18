# Autenticación, Configuración y Rate Limiting

## 1. Visión General de la API
La API REST de GitHub permite a los desarrolladores interactuar mediante programación con repositorios, organizaciones, usuarios y flujos de trabajo de GitHub. Todas las solicitudes deben realizarse a través de HTTPS.

* **URL Base Oficial:** `https://api.github.com`
* **Formato de Intercambio de Datos:** JSON (JavaScript Object Notation) para solicitudes y respuestas.
* **Versión de la API:** Se recomienda fijar la versión mediante el encabezado HTTP correspondiente. La versión actual estable es `2022-11-28`.

---

## 2. Encabezados HTTP Estándar
Para garantizar la compatibilidad y consistencia en las respuestas, se recomienda que cada solicitud a la API REST de GitHub incluya los siguientes encabezados. El único estrictamente obligatorio es `User-Agent`; `Authorization` sólo es necesario en peticiones autenticadas, y `Accept` y `X-GitHub-Api-Version` son los valores recomendados por GitHub:

| Encabezado | Valor Recomendado | Propósito |
| :--- | :--- | :--- |
| `Accept` | `application/vnd.github+json` | Especifica la versión del tipo de medio oficial de GitHub para respuestas JSON. |
| `Authorization` | `Bearer <TOKEN_PERSONAL>` | Proporciona las credenciales de acceso para peticiones autenticadas. |
| `X-GitHub-Api-Version` | `2022-11-28` | Fija la versión de la especificación de la API para evitar incompatibilidades. |
| `User-Agent` | `<NOMBRE_APLICACION_O_USUARIO>` | Obligatorio por política de GitHub. Peticiones sin `User-Agent` son rechazadas con error HTTP 403. |

### Ejemplo de Solicitud HTTP con cURL:
```bash
curl -L \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ghp_ejemploToken123456" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -H "User-Agent: MiApp-Cliente-IA" \
  https://api.github.com/user
```

---

## 3. Métodos y Tipos de Autenticación
GitHub soporta varios mecanismos de autenticación según el caso de uso:

### 3.1 Personal Access Tokens (PAT)
* **Tokens Clásicos (`ghp_...`):** Poseen un conjunto amplio de scopes predefinidos (`repo`, `read:org`, `delete_repo`, etc.). Tienen un alcance global sobre todos los recursos del usuario.
* **Fine-Grained Tokens (`github_pat_...`):** Tokens de grano fino introducidos para máxima seguridad. Permiten seleccionar repositorios específicos y otorgar permisos de solo lectura o lectura/escritura únicamente a endpoints delimitados (ej. sólo lectura de Issues).

### 3.2 GitHub App Tokens
Utilizados para automatizaciones empresariales y bots. Utilizan un flujo JWT (JSON Web Token) para generar tokens temporales de instalación (`ghs_...`).

### 3.3 Acceso Sin Autenticación
Permitido únicamente para lectura de recursos públicos (`GET`). Altamente restringido en capacidad operativa por cuotas de uso.

---

## 4. Cuotas de Uso y Límites de Tasa (Rate Limiting)
GitHub aplica límites estrictos para proteger la infraestructura y garantizar equidad en el consumo de recursos.

### 4.1 Tipos de Límites Principales
1. **Peticiones no autenticadas:**
   * Límite: **60 solicitudes por hora** por dirección IP de origen.
   * Aplica a consultas públicas generales.
2. **Peticiones autenticadas (Tokens Personales / OAuth):**
   * Límite: **5,000 solicitudes por hora** por usuario autenticado.
   * Aplica a todos los endpoints regulares de la REST API.
3. **Límite de Búsqueda (Search API):**
   * Límite dedicado y separado de los endpoints regulares.
   * Autenticado: **30 solicitudes por minuto**.
   * No autenticado: **10 solicitudes por minuto**.

* **Al exceder el límite:** GitHub responde con `403 Forbidden` o `429 Too Many Requests` y `x-ratelimit-remaining` en `0`. Las solicitudes vuelven a aceptarse cuando se alcanza el instante indicado en `x-ratelimit-reset`.

### 4.2 Encabezados de Respuesta para Monitoreo de Cuota
Cada respuesta HTTP devuelta por GitHub contiene cabeceras que informan el estado exacto de la cuota:

* `x-ratelimit-limit`: Número máximo de solicitudes permitidas en la ventana de tiempo (ej. 5000).
* `x-ratelimit-remaining`: Número de solicitudes disponibles restantes en la ventana actual.
* `x-ratelimit-reset`: Marca de tiempo en formato Epoch Unix (segundos desde el 1 de enero de 1970 UTC) en la que se reiniciará la cuota.
* `x-ratelimit-used`: Cantidad de solicitudes ya consumidas en la ventana presente.

### 4.3 Endpoint Dedicado de Estado de Tasa
Para consultar el estado de la cuota sin consumir solicitudes del límite general:
* **Método:** `GET`
* **Ruta:** `/rate_limit`
* **Respuesta Ejemplo:**
```json
{
  "resources": {
    "core": {
      "limit": 5000,
      "remaining": 4985,
      "reset": 1718000000,
      "used": 15
    },
    "search": {
      "limit": 30,
      "remaining": 30,
      "reset": 1717996500,
      "used": 0
    }
  }
}
```

---

## 5. Códigos de Estado HTTP y Manejo de Errores

| Código HTTP | Descripción Oficial | Diagnóstico y Acción Requerida |
| :--- | :--- | :--- |
| **200 OK** | Solicitud exitosa | Operación completada; el cuerpo contiene los datos solicitados. |
| **201 Created** | Recurso creado | Operaciones `POST` exitosas (creación de repo, issue, etc.). |
| **204 No Content** | Operación exitosa sin cuerpo | Típico en eliminación (`DELETE`) o acciones sin datos de retorno. |
| **304 Not Modified** | Caché válida | No hay cambios en el recurso (usando cabeceras `If-None-Match`). |
| **401 Unauthorized** | Autenticación requerida o fallida | Token inválido, expirado, malformado o ausente. |
| **403 Forbidden** | Acceso prohibido / Rate limit excedido | Token sin permisos para el recurso o cuota de rate limit en 0. |
| **429 Too Many Requests** | Demasiadas solicitudes | Rate limit primario o secundario excedido; esperar hasta `x-ratelimit-reset` (o lo indicado en `retry-after`) antes de reintentar. |
| **404 Not Found** | Recurso inexistente o privado | El recurso no existe o el token no tiene visibilidad sobre él. |
| **422 Unprocessable Entity** | Error de validación semántica | El JSON enviado contiene campos inválidos, faltan obligatorios o formato erróneo. |
