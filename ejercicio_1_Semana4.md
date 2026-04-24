
## 1. Implementación de Consultas (Endpoints)

Para garantizar una experiencia de usuario fluida en nuestro catálogo, hemos elegido los puntos de acceso más eficientes de la API de CheapShark:

* **Búsqueda dinámica por título:** Utilizaremos el endpoint /games con el parámetro title. Esto nos permite realizar búsquedas bajo demanda según lo que el usuario escriba, obteniendo resultados en tiempo real.
    * **Ejemplo de consulta:** GET https://www.cheapshark.com/api/1.0/games?title=batman
* **Recuperación de juegos por ID:** Para gestionar la biblioteca personalizada del usuario, consultaremos el mismo endpoint /games pero utilizando el parámetro ids. Esto nos permite recuperar la información actualizada de varios juegos simultáneamente (separados por comas) basándonos en el gameID que hayamos almacenado previamente.
    * **Ejemplo de consulta:** GET https://www.cheapshark.com/api/1.0/games?ids=128,129,130

## 2. Seguridad y Normas de Uso

Uno de los puntos clave de CheapShark es que ofrece una API pública, lo que significa que **no requiere tokens de acceso ni claves privadas**. Sin embargo, esto implica una responsabilidad en su uso:

* **Respeto al Rate Limiting:** La API está optimizada para interacciones directas del usuario. Las políticas de CheapShark prohíben explícitamente el "scraping" masivo o el almacenamiento de su base de datos completa. Un uso abusivo o automatizado podría resultar en el bloqueo permanente de nuestra IP. Por ello, nuestra arquitectura está diseñada para consultar solo lo necesario en el momento justo.

## 3. Estrategia Arquitectónica y Decisiones de Diseño

Hemos definido una serie de principios para que nuestra aplicación sea escalable, rápida y segura:

### Gestión de Identificadores
Cuando un usuario añade un juego a su lista, no duplicamos toda la información. Simplemente guardamos un `external_game_id` vinculado al `gameID` de CheapShark. Esto garantiza que nuestra base de datos sea ligera y que siempre podamos referenciar el origen exacto de los datos.

### Optimización del Flujo de Datos (Backend a Frontend)
Aunque la API externa nos entregue mucha información, nuestro backend solo enviará al frontend lo estrictamente necesario (ID, título, imagen y precio). Esto lo hacemos por tres motivos principales:

1.  **Velocidad:** Menos datos equivalen a respuestas más rápidas, algo vital para usuarios en dispositivos móviles.
2.  **Consistencia:** Al filtrar los datos en el backend, el frontend siempre recibe el mismo formato, independientemente de si CheapShark decide cambiar su estructura interna en el futuro.
3.  **Arquitectura Limpia:** Aplicamos el patrón **BFF (Backend For Frontend)**, donde nuestro servidor actúa como un filtro inteligente que adapta los datos brutos a las necesidades específicas de nuestra interfaz.



### ¿Por qué no guardamos el catálogo en nuestra propia base de datos?
Mantener una copia local del catálogo de CheapShark sería contraproducente por las siguientes razones:

* **Información en tiempo real:** Los precios y ofertas de los juegos son extremadamente volátiles. Tener una base de datos local nos obligaría a realizar sincronizaciones constantes (procesos pesados de tipo cron) que rara vez estarían al día.
* **Eficiencia de recursos:** El catálogo global es inmenso. Delegar el almacenamiento y la indexación a un servicio especializado como CheapShark nos permite centrar nuestra infraestructura en lo que realmente importa: la experiencia de nuestros usuarios.
* **Simplicidad operativa:** Al consultar bajo demanda, nos aseguramos de que el usuario siempre vea el precio "fresco" y las ofertas vigentes sin que nosotros tengamos que gestionar el mantenimiento técnico de esa enorme masa de datos.