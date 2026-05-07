# Guion para video del backend steamlike_backend

Duracion objetivo: 3 a 5 minutos.

## Preparacion antes de grabar

1. Abrir VS Code con el repositorio en `main`.
2. Ejecutar el proyecto:

```bash
docker compose up --build
```

3. Tener a mano una herramienta para probar endpoints: navegador, Thunder Client, Postman o terminal con `curl`.
4. URLs principales:
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:3000`
   - Health check: `http://localhost:8000/api/health/`

## Guion narrado

### 0:00 - 0:20 | Presentacion

"En este video voy a explicar el funcionamiento del backend del proyecto `steamlike_backend`, una aplicacion tipo biblioteca de videojuegos llamada Nexus Play. Voy a mostrar primero que el backend esta en ejecucion, despues un flujo completo de uso con registro, busqueda de juegos y gestion de biblioteca, y por ultimo un caso de error provocado para comprobar como responde el sistema."

### 0:20 - 0:55 | Integracion de ramas

"Antes de probar el backend, el repositorio se ha dejado en un estado estable en la rama `main`. Se revisaron e integraron las ramas de desarrollo del proyecto, incluyendo ramas de semanas anteriores como `dwes-semana1`, `dwes-semana2`, `dwes-semana3`, `optativa-semana1`, `optativa-semana3`, `optativa-semana5` y `devops-semana1`."

"Durante la integracion aparecieron conflictos historicos relacionados con migraciones, configuracion de Django, Docker, Redis, frontend y despliegue. En especial, la rama `devops-semana1` estaba desactualizada y habria eliminado funcionalidades actuales como el frontend integrado, Render, Redis, Maileroo y el devcontainer. Por eso se resolvio conservando el estado actual de `main`, que ya contiene las funcionalidades mas recientes y verificadas."

"Tras la integracion se comprobaron los tests y el proyecto sigue funcionando correctamente."

Mostrar en pantalla:

```bash
git branch --no-merged HEAD
python manage.py test
```

Frase corta:

"La comprobacion final indica que no quedan ramas locales pendientes de fusionar en `main` y que los tests del backend pasan correctamente."

### 0:55 - 1:20 | Backend en ejecucion

"Ahora muestro el backend ejecutandose. El proyecto se puede levantar con Docker, lo que crea los servicios necesarios: Django, PostgreSQL, Redis y el frontend. Django aplica las migraciones y arranca el servidor en el puerto 8000."

Mostrar:

```bash
docker compose up --build
```

Despues probar:

```bash
curl http://localhost:8000/api/health/
```

Explicar:

"El endpoint `/api/health/` devuelve `{\"status\":\"ok\"}`, asi que el backend esta activo y preparado para recibir peticiones."

### 1:20 - 2:45 | Flujo completo de uso

"Voy a realizar un flujo completo de uso del sistema. Primero registro un usuario. El endpoint utilizado es `POST /api/auth/register/`. Envio un nombre de usuario, una contrasena y un correo electronico."

Ejemplo:

```json
{
  "username": "usuario_video",
  "password": "password123",
  "email": "usuario_video@example.com"
}
```

"El resultado esperado es una respuesta `201 Created` con el id, username y email del usuario. Internamente, el backend crea el usuario de Django y llama al servicio de email para enviar un mensaje de bienvenida mediante Maileroo, siempre que las variables de entorno esten configuradas."

"Despues inicio sesion con `POST /api/auth/login/`. Si las credenciales son correctas, el backend crea una sesion y devuelve el usuario autenticado."

Ejemplo:

```json
{
  "username": "usuario_video",
  "password": "password123"
}
```

"A continuacion consulto el usuario actual con `GET /api/users/me/`. Esta prueba confirma que la sesion esta activa."

"El siguiente paso es buscar juegos en el catalogo externo. Para eso uso `GET /api/catalog/search/?q=portal`. El backend consulta CheapShark, normaliza la respuesta y devuelve juegos con `external_game_id`, `title` y `thumb`. Ademas, el servicio usa Redis para cachear las busquedas y mejorar el rendimiento."

"Con uno de esos identificadores creo una entrada en mi biblioteca usando `POST /api/library/entries/`."

Ejemplo:

```json
{
  "external_game_id": "102495",
  "status": "playing",
  "hours_played": 3
}
```

"El resultado esperado es `201 Created`. El backend valida que el usuario este autenticado, comprueba que el juego exista en el catalogo externo y guarda la entrada asociada al usuario."

"Por ultimo consulto `GET /api/library/entries/` para ver la biblioteca del usuario. Debe aparecer la entrada creada con su estado y horas jugadas."

### 2:45 - 3:35 | Caso de error provocado

"Ahora provoco un error para comprobar la validacion. Intento crear una entrada incompleta, sin el campo `hours_played`."

Ejemplo:

```json
{
  "external_game_id": "102495",
  "status": "playing"
}
```

"El backend responde con `400 Bad Request` y un JSON de error de validacion. En `details` indica que `hours_played` es un campo obligatorio. Esta respuesta es adecuada porque no permite guardar datos incompletos y explica cual es el problema."

"Tambien hay otros errores controlados: si no estoy autenticado devuelve `401 unauthorized`; si intento consultar una entrada que no existe devuelve `404 not_found`; y si repito un juego en la misma biblioteca devuelve `duplicate_entry`."

### 3:35 - 4:20 | Logs del backend

"Mientras se ejecutan estas operaciones, el backend genera logs. En las busquedas de catalogo aparecen eventos como `cache_lookup`, `cache_miss`, `provider_request`, `cache_write` y `cache_hit`. Esto permite saber si el resultado vino de Redis o de la API externa."

"En el envio de email aparecen logs como `email intento de envio`, `email envio OK` o errores de configuracion, red o proveedor. Estos registros ayudan a detectar rapidamente si Maileroo esta configurado o si el proveedor devuelve un fallo."

"Una mejora posible seria anadir un identificador de peticion para seguir una operacion completa de principio a fin, y registrar el endpoint o metodo HTTP en todos los eventos importantes."

### 4:20 - 4:45 | Cierre

"Como comprobacion final, el backend arranca correctamente, las migraciones se aplican, los endpoints principales responden y los tests automatizados pasan. Por tanto, despues de integrar las ramas, el proyecto queda en un estado estable y las funcionalidades principales siguen disponibles: autenticacion, busqueda de juegos, gestion de biblioteca, cache con Redis, validacion de errores y envio de emails de bienvenida mediante Maileroo."

## Resumen de pruebas mencionadas

| Prueba | Endpoint | Datos enviados | Resultado esperado |
| --- | --- | --- | --- |
| Health check | `GET /api/health/` | No aplica | `200 {"status":"ok"}` |
| Registro | `POST /api/auth/register/` | `username`, `password`, `email` | `201` con usuario creado |
| Login | `POST /api/auth/login/` | `username`, `password` | `200` con sesion activa |
| Busqueda catalogo | `GET /api/catalog/search/?q=portal` | Query `q` | Lista de juegos |
| Crear entrada | `POST /api/library/entries/` | `external_game_id`, `status`, `hours_played` | `201` con entrada creada |
| Listar biblioteca | `GET /api/library/entries/` | Cookie de sesion | Lista de entradas del usuario |
| Error validacion | `POST /api/library/entries/` incompleto | Falta `hours_played` | `400 validation_error` |

## Maileroo en Render

El codigo ya envia email de bienvenida al registrarse un usuario. Para que funcione en Render, el servicio debe tener estas variables de entorno:

```text
MAILEROO_API_KEY=<sending-key-de-maileroo>
MAILEROO_FROM_ADDRESS=david@45f07c6711c75cfe.maileroo.org
MAILEROO_FROM_NAME=Nexus Play
MAILEROO_API_URL=https://smtp.maileroo.com/api/v2/emails
MAILEROO_TIMEOUT=10
```

No se debe subir la sending key real al repositorio. Debe guardarse en Render Dashboard, dentro del servicio `steamlike-backend`, en la seccion `Environment`.
