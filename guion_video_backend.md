# Guion para video del backend en Render

Duracion objetivo: 3 a 5 minutos.

URL de produccion:

```text
https://steamlike-backend-1.onrender.com
```

## Preparacion antes de grabar

Ten abiertas estas pantallas:

1. Render Dashboard del servicio `steamlike-backend`.
2. La web publica: `https://steamlike-backend-1.onrender.com/`.
3. Una herramienta para probar endpoints: Thunder Client, Postman o terminal.
4. La pagina de logs de Render: servicio `steamlike-backend` > `Logs`.

Si Render esta dormido por el plan gratuito, la primera peticion puede tardar. Espera a que despierte antes de empezar a grabar.

## Guion narrado

### 0:00 - 0:20 | Presentacion

"En este video voy a mostrar el backend del proyecto `steamlike_backend` funcionando desplegado en Render. La aplicacion se llama Nexus Play y permite registrar usuarios, iniciar sesion, buscar juegos en un catalogo externo y gestionar la biblioteca personal de videojuegos."

"Voy a probarlo directamente desde la URL publica de Render, no en local, para demostrar que el despliegue esta funcionando correctamente."

Mostrar en pantalla:

```text
https://steamlike-backend-1.onrender.com
```

### 0:20 - 0:55 | Integracion de ramas

"Antes de probar el backend, el repositorio se dejo estable en la rama `main`. Se integraron las ramas de desarrollo del proyecto: `dwes-semana1`, `dwes-semana2`, `dwes-semana3`, `optativa-semana1`, `optativa-semana3`, `optativa-semana5` y `devops-semana1`."

"Durante la integracion se revisaron conflictos relacionados con migraciones, configuracion de Django, Docker, Redis, frontend, Render y envio de emails. La rama `devops-semana1` era una rama antigua y, si se aceptaban sus cambios directamente, eliminaba funcionalidades actuales como el frontend integrado, la configuracion de Render, Redis, Maileroo y el devcontainer. Por eso se fusiono conservando el estado actual de `main`, que es la version completa y verificada."

"Despues de la integracion se comprobaron los tests del backend y el proyecto quedo funcionando correctamente."

Si quieres mostrarlo rapidamente:

```bash
git branch --no-merged HEAD
python manage.py test
```

Frase:

"La comprobacion muestra que no quedan ramas locales pendientes de fusionar y que los tests automatizados pasan."

### 0:55 - 1:20 | Backend desplegado en Render

"Ahora compruebo que el backend esta vivo en Render. Primero abro la aplicacion publica. Render esta sirviendo el frontend de Nexus Play desde el mismo servicio Django."

Mostrar navegador:

```text
https://steamlike-backend-1.onrender.com/
```

"Despues pruebo el endpoint de salud del backend."

Endpoint:

```http
GET https://steamlike-backend-1.onrender.com/api/health/
```

Resultado esperado:

```json
{"status": "ok"}
```

Frase:

"Este `200 OK` confirma que el servicio de Render esta levantado y que Django responde correctamente."

### 1:20 - 2:50 | Flujo completo de uso del sistema

"Ahora realizo un flujo completo. Primero registro un usuario nuevo usando el endpoint `POST /api/auth/register/`."

Endpoint:

```http
POST https://steamlike-backend-1.onrender.com/api/auth/register/
```

Body recomendado:

```json
{
  "username": "usuario_video_01",
  "password": "password123",
  "email": "tu_correo_real@example.com"
}
```

Narracion:

"El resultado esperado es `201 Created`, con el id, username y email del usuario. Internamente el backend valida los datos, crea el usuario en la base de datos PostgreSQL de Render y llama al servicio de Maileroo para enviar el email de bienvenida."

"Despues inicio sesion con el usuario creado."

Endpoint:

```http
POST https://steamlike-backend-1.onrender.com/api/auth/login/
```

Body:

```json
{
  "username": "usuario_video_01",
  "password": "password123"
}
```

Narracion:

"Si las credenciales son correctas, el backend devuelve `200 OK` y crea una sesion. En Postman o Thunder Client se guarda la cookie de sesion, que se utilizara en las siguientes peticiones."

"Compruebo ahora el usuario autenticado."

Endpoint:

```http
GET https://steamlike-backend-1.onrender.com/api/users/me/
```

Resultado esperado:

```json
{
  "id": 1,
  "username": "usuario_video_01"
}
```

"El siguiente paso es buscar juegos en el catalogo externo. Uso el endpoint `GET /api/catalog/search/` con la busqueda `portal`."

Endpoint:

```http
GET https://steamlike-backend-1.onrender.com/api/catalog/search/?q=portal
```

Resultado real esperado:

```json
[
  {
    "external_game_id": "82",
    "title": "Portal",
    "thumb": "https://..."
  },
  {
    "external_game_id": "36",
    "title": "Portal 2",
    "thumb": "https://..."
  }
]
```

Narracion:

"Aqui el backend consulta la API externa de CheapShark, normaliza los datos y devuelve una lista simple con id externo, titulo e imagen. Ademas, el servicio tiene cache con Redis para reutilizar busquedas cuando esta disponible."

"Con uno de esos juegos creo una entrada en mi biblioteca."

Endpoint:

```http
POST https://steamlike-backend-1.onrender.com/api/library/entries/
```

Body:

```json
{
  "external_game_id": "82",
  "status": "playing",
  "hours_played": 3
}
```

Narracion:

"El resultado esperado es `201 Created`. El backend comprueba que el usuario esta autenticado, valida que el juego existe en el catalogo externo y guarda la entrada asociada al usuario."

"Por ultimo consulto mi biblioteca."

Endpoint:

```http
GET https://steamlike-backend-1.onrender.com/api/library/entries/
```

Resultado esperado:

```json
[
  {
    "id": 1,
    "external_game_id": "82",
    "status": "playing",
    "hours_played": 3
  }
]
```

Narracion:

"La respuesta muestra las entradas de la biblioteca del usuario autenticado, por lo que el flujo completo funciona en Render: registro, login, busqueda externa, creacion y listado."

### 2:50 - 3:35 | Caso de error provocado

"Ahora provoco un error para comprobar la validacion del backend. Intento crear una entrada incompleta, sin `hours_played`."

Endpoint:

```http
POST https://steamlike-backend-1.onrender.com/api/library/entries/
```

Body incorrecto:

```json
{
  "external_game_id": "82",
  "status": "playing"
}
```

Resultado esperado:

```json
{
  "error": "validation_error",
  "message": "Datos de entrada invalidos",
  "details": {
    "hours_played": "Campo obligatorio."
  }
}
```

Narracion:

"La respuesta correcta es `400 Bad Request`. El backend no guarda datos incompletos y explica claramente que falta el campo `hours_played`."

Puedes mencionar rapidamente otros errores:

"Tambien hay otros errores controlados: si no hay sesion devuelve `401 unauthorized`; si el id de entrada no existe devuelve `404 not_found`; si se intenta repetir un juego en la misma biblioteca devuelve `duplicate_entry`; y si el catalogo externo falla, el backend responde con errores controlados `502` o `503`."

### 3:35 - 4:20 | Logs en Render

Mostrar Render Dashboard > servicio `steamlike-backend` > `Logs`.

"Ahora reviso los logs del servicio en Render. Aqui se observan las peticiones HTTP que llegan al backend y los mensajes internos de la aplicacion."

"En las busquedas de catalogo aparecen eventos como `cache_lookup`, `cache_miss`, `provider_request`, `cache_write` o `cache_hit`. Estos logs permiten entender si la busqueda se resolvio usando Redis o si se consulto la API externa."

"En el registro de usuario, si Maileroo esta configurado, aparecen logs como `email intento de envio` y `email envio OK`. Si falta la configuracion o hay un problema con el proveedor, aparece un log de error indicando si es un fallo de configuracion, red o respuesta del proveedor."

"Estos logs son utiles para detectar problemas, porque permiten seguir que ocurre internamente sin acceder directamente al servidor."

Mejora posible:

"Como mejora, seria util anadir un identificador de peticion para relacionar todos los logs de una misma operacion y registrar siempre el metodo HTTP y el endpoint."

### 4:20 - 4:50 | Cierre

"Como conclusion, el backend funciona correctamente en Render. El servicio responde al health check, permite registrar usuarios, iniciar sesion, buscar juegos en la API externa, crear entradas de biblioteca y controlar errores de validacion."

"Ademas, tras integrar las ramas de desarrollo, los tests siguen pasando y el backend mantiene sus funcionalidades principales: autenticacion, biblioteca de usuario, catalogo externo, cache con Redis, logs y envio de emails con Maileroo."

"Con esto queda comprobado que el proyecto esta desplegado y operativo en un entorno real."

## Pruebas que puedes incluir en el documento

| Prueba | Endpoint en Render | Datos enviados | Resultado esperado | Correcto |
| --- | --- | --- | --- | --- |
| Health check | `GET /api/health/` | No aplica | `200 {"status":"ok"}` | Si |
| Registro | `POST /api/auth/register/` | `username`, `password`, `email` | `201` con usuario creado | Si |
| Login | `POST /api/auth/login/` | `username`, `password` | `200` con cookie de sesion | Si |
| Usuario actual | `GET /api/users/me/` | Cookie de sesion | Datos del usuario | Si |
| Buscar catalogo | `GET /api/catalog/search/?q=portal` | Query `q` | Lista de juegos | Si |
| Crear biblioteca | `POST /api/library/entries/` | `external_game_id`, `status`, `hours_played` | `201` con entrada creada | Si |
| Listar biblioteca | `GET /api/library/entries/` | Cookie de sesion | Entradas del usuario | Si |
| Error provocado | `POST /api/library/entries/` incompleto | Falta `hours_played` | `400 validation_error` | Si |

## Notas para Maileroo en Render

Para que se envie el correo de bienvenida al registrarse en Render, el servicio debe tener estas variables en Render Dashboard > `steamlike-backend` > `Environment`:

```text
MAILEROO_API_KEY=<sending-key-de-maileroo>
MAILEROO_FROM_ADDRESS=david@45f07c6711c75cfe.maileroo.org
MAILEROO_FROM_NAME=Nexus Play
MAILEROO_API_URL=https://smtp.maileroo.com/api/v2/emails
MAILEROO_TIMEOUT=10
```

Despues pulsa `Save, rebuild, and deploy`.

La clave real no debe subirse al repositorio. En `render.yaml` solo se deja `MAILEROO_API_KEY` con `sync: false` para indicar que existe, pero el valor se guarda manualmente en Render.
