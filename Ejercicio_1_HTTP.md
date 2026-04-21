# Ejercicio 1: Métodos y Códigos de Estado HTTP
 
### GET (Obtener / Leer)
Sirve para solicitar información o datos al servidor sin modificarlos. 


**En el proyecto:** Se utiliza en la función **listar_entradas_biblioteca** (`GET /api/library/entries/`) para pedirle al servidor todos los juegos que el usuario tiene guardados en su biblioteca. También se usa en `usuario_actual` para obtener los datos de la sesión o en `health` para ver el estado del servidor. Es una petición "segura" porque puedes hacerla mil veces sin alterar la base de datos.

### POST (Crear / Enviar)
Se usa para **mandar datos** al servidor con la intención de crear un nuevo recurso o realizar una acción.
* **Caso en el proyecto:** En `crear_entrada_biblioteca` (`POST /api/library/entries/`), le enviamos un JSON con datos (`external_game_id`, `status`, `hours_played`) para crear un nuevo registro en la base de datos. También se usa en `registrar_usuario` e `iniciar_sesion` (`POST /api/auth/register/` y `POST /api/auth/login/`), ya que estamos enviando de forma segura nuestro usuario y contraseña para generar un nuevo usuario o una sesión.

### PATCH (Modificación Parcial)
Está pensado para realizar **actualizaciones parciales** en un recurso. En lugar de mandar absolutamente todos los campos para machacarlos, mandas solo aquellos que quieres cambiar.
* **Caso en el proyecto:** En `actualizar_entrada_biblioteca` (`PATCH /api/library/entries/{id}/`), lo utilizamos si un usuario que estaba en estado "playing" y con 10 "hours_played", decide actualizar **solo** las horas jugadas a 12. Se le envía un JSON con `{"hours_played": 12}` y se actualiza en base de datos.

### PUT (Reemplazo Completo)
Es para modificar un recurso pero **reemplazándolo de forma completa**. Es decir, mandaríamos todo el objeto de un plumazo. 
* **Caso en el proyecto:** Aunque no lo estamos utilizando como tal, si lo tuviéramos, forzaría a enviar desde el cliente *todos* los campos (status, horas, id_externo...) incluso cuando queremos cambiar solo el estado. Por eso en nuestro caso de uso encaja mejor `PATCH`.

### DELETE (Borrar)
Como su nombre indica, se utiliza pura y duramente para **eliminar un recurso**.
* **Caso en el proyecto:** Aunque todavía no se haya implementado una vista para borrar, su caso de uso aquí correspondería a eliminar definitivamente un juego de nuestra biblioteca con una petición como `DELETE /api/library/entries/{id}/`.




## Códigos de Estado HTTP

Los códigos de estado son un número de 3 cifras devuelto por el servidor que nos resume de un solo vistazo el resultado de nuestra petición HTTP. Se dividen en varias familias (2xx éxito, 4xx errores del cliente, 5xx errores del servidor).

### Códigos de Éxito (2xx)

* **200 OK:**  Significa "Todo ha ido bien y te devuelvo lo que pediste".
    * **En el proyecto:** Aparece cuando listamos bien los juegos, cuando vemos el detalle de uno (`JsonResponse(..., status=200)`), al loguearse correctamente, o cuando hicimos bien una edición parcial (PATCH). 
* **201 Created:** Significa "Todo ha sido un éxito y además **he creado** algo nuevo".
    * **En el proyecto:** Se devuelve explícitamente en `crear_entrada_biblioteca` cuando el juego acaba de guardarse por primera vez en la BD (`JsonResponse(..., status=201)`), o tras conseguir crear correctamente un nuevo usuario.
* **204 No Content:** Significa "Éxito, pero no tengo nada que responderte".
    * **En el proyecto:** Se suele utilizar si el backend procesa con éxito un borrado (DELETE). Elimina tu juego de la biblioteca y te responde "Hecho" devolviendo un `204`, en lugar de un JSON vacío.

### Errores del Cliente (4xx)

* **400 Bad Request:** Significa "Me has mandado algo mal o de forma incorrecta y el servidor no te entiende".
    * **En el proyecto:** Se maneja muchísimo en la función `error_validacion`. Se dispara si mandamos un JSON inválido, si nos falta enviar el campo obligatorio `external_game_id` para añadir un juego o pusimos el valor de `hours_played` en negativo.
* **401 Unauthorized:** Significa "No has iniciado sesión o me mandas credenciales inválidas".
    * **En el proyecto:** Cuando la funcion llama a `error_no_autorizado()`. Te pasa si intentas crear un juego o listar tu biblioteca y en realidad no te habías autenticado (invitado), o si escribiste mal la contraseña en el POST de `/api/auth/login/`.
* **403 Forbidden:** Mencionable junto con el anterior. Implica "Sé quién eres (estás autenticado) pero **no tienes permisos** para hacer esto".
    * **En el proyecto:** Se utilizaría idealmente si un usuario intentase acceder al panel nativo de administradores de base de datos de Django, o si en código estricto limitamos el acceso de algunos endpoints en base al rol de cada persona (ej: usuario normal queriendo borrar a otro usuario).
* **404 Not Found:** Significa "Lo que me estás pidiendo o la URL no existe".
    * **En el proyecto:** Aparece con la función `error_no_encontrado()`. Si haces GET al `entry_id` "9999" y no tienes ningún juego con esa ID, el servidor de nuestro proyecto te devuelve de forma elegante un modelo en JSON diciendo que no se localizó la ID insertada (404). Y también si tratamos de editar el de otro usuario.
* **409 Conflict:** Significa "Tu solicitud no se puede procesar porque existe un conflicto con el estado actual (usualmente cosas duplicadas)".
    * **En el proyecto:** Te idealmente debería utilizar cuando intentas agregar un juego que ya agregaste antes, saltando nuestro temido `IntegrityError` de la validación unique. *(Actualmente nuestro código responde 400 con `error_duplicado`, pero técnicamente para recursos duplicados donde entra en conflicto otro ya existente, encaja como anillo al dedo el código 409).*

### Errores del Servidor (5xx)

* **500 Internal Server Error:** Significa "El servidor se rompió por algún lugar inesperadamente pero la culpa no es por tus datos de cliente".
    * **En el proyecto:** Aparece si el código Python "crashea" sin un `try/except`. Por ejemplo, en caso de cometer un error tipográfico en la lógica y tratar de acceder al atributo de un string que en realidad era None o intentar invocar a base de datos y la conexión en el servidor había fallado (Docker apagado).
