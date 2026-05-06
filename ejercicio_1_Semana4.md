# Ejercicio 1 - Integración del catálogo CheapShark

## Endpoints de CheapShark que se usan

La documentación pública de CheapShark indica que el recurso principal para juegos es:

```text
GET https://www.cheapshark.com/api/1.0/games
```

Para buscar juegos por texto se usa el parámetro `title`:

```text
GET https://www.cheapshark.com/api/1.0/games?title=batman
```

La respuesta es una lista de juegos. Para nuestro backend interesan solo estos campos:

- `gameID`: identificador externo del juego.
- `external`: título del juego.
- `thumb`: miniatura.

Para consultar varios juegos por ID se usa el parámetro `ids`, con los `gameID` separados por comas:

```text
GET https://www.cheapshark.com/api/1.0/games?ids=128,129,130
```

La respuesta es un objeto cuyas claves son los IDs solicitados. Dentro de cada juego se usa `info.title` y `info.thumb`.

## Autenticación y aspectos relevantes

CheapShark ofrece una API pública y no requiere API key ni token para estas consultas.

Aun así, el backend debe tratarla como un proveedor externo:

- Puede no responder por timeout o error de red.
- Puede responder con un error HTTP.
- Puede devolver datos con un formato inesperado.
- No se debe exponer al frontend la respuesta cruda ni errores internos del proveedor.

Por eso el backend traduce esos casos a JSON estable:

- `503 external_service_unavailable` si no hay respuesta.
- `502 external_service_error` si el proveedor responde con error o datos inválidos.
- `400 invalid_external_game_id` si el ID usado al crear una entrada de biblioteca no existe.

## Uso de `external_game_id`

En nuestra base de datos no se guarda el juego completo. Solo se guarda:

```text
external_game_id = gameID de CheapShark
```

Ese valor permite relacionar una entrada de nuestra biblioteca con un juego del catálogo externo.

## Por qué el frontend recibe información mínima

El backend solo devuelve:

```json
{
  "external_game_id": "128",
  "title": "Game title",
  "thumb": "https://..."
}
```

Esto mantiene un contrato estable entre frontend y backend. CheapShark puede devolver muchos más campos, pero el frontend no los necesita para buscar juegos o mostrar una biblioteca enriquecida. Al filtrar la respuesta en el backend:

- Se reduce el tamaño de la respuesta.
- Se evita acoplar el frontend a la estructura interna de CheapShark.
- Se controla qué información externa se expone.

## Por qué el catálogo no se guarda en nuestra base de datos

El catálogo no pertenece a nuestra aplicación. Guardarlo completo duplicaría datos externos y obligaría a mantenerlos sincronizados.

La base de datos del sistema debe almacenar solo información propia de la aplicación: usuarios, entradas de biblioteca, estado y horas jugadas. El título y la miniatura se consultan bajo demanda al catálogo externo cuando hacen falta.

## Resumen para explicar en clase

Nuestro backend actúa como intermediario entre el frontend y CheapShark. El frontend nunca llama directamente a CheapShark. Para buscar se usa `/games?title=...`; para resolver varios IDs se usa `/games?ids=...`. En la biblioteca solo guardamos el `gameID` como `external_game_id`, y cuando necesitamos mostrar título o miniatura se llama al endpoint `resolve`.

Fuentes:

- [CheapShark API docs](https://apidocs.cheapshark.com/)
- [CheapShark public Postman workspace](https://www.postman.com/cheapshark/workspace/cheapshark-s-public-workspace/documentation/530355-334a254b-aae7-4450-a352-b573b31403fe)
