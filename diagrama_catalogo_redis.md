# Diagrama del flujo de catalogo con Redis

Archivo de diagrama: `diagrama_catalogo_redis.svg`

## Flujo normal

1. El frontend llama a `GET /api/catalog/search/?q=texto`.
2. La vista Django valida que `q` exista y delega en `CatalogService`.
3. `CatalogService` consulta Redis con una clave derivada de la busqueda.
4. Si Redis tiene datos, devuelve la lista cacheada sin llamar a CheapShark.
5. Si Redis no tiene datos, consulta CheapShark, transforma la respuesta al contrato interno y guarda el resultado en Redis con TTL.
6. La vista devuelve el mismo JSON de siempre: `external_game_id`, `title`, `thumb`.

## Flujo con fallo del proveedor

Si CheapShark devuelve error, datos invalidos o no responde, el servicio lo traduce a errores controlados:

- Timeout o red: `503 external_service_unavailable`.
- Error HTTP o formato invalido: `502 external_service_error`.

Si existe una copia cacheada de respaldo en Redis, `CatalogService` la usa y registra en logs que ha usado Redis por fallo del proveedor.

## Uso de Redis

Redis actua como cache temporal del catalogo externo. No sustituye a CheapShark y no persiste datos en la base de datos del sistema. El frontend no sabe si la respuesta viene de Redis o de CheapShark porque el formato JSON no cambia.

## Logs relevantes

El servicio registra:

- Consulta a Redis.
- Uso de datos cacheados.
- Consulta a CheapShark.
- Escritura en Redis.
- Uso de Redis por fallo del proveedor.
