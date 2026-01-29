```instructions
# Instrucciones para agentes AI (Copilot)

Propósito: ayudar a agentes AI a ser productivos rápidamente en este repo estático.

- Resumen rápido:
  - Proyecto minimalista: sitio estático servido desde `index.html` con lógica en `script.js` que carga `data.csv` en el cliente.
  - No hay paso de build ni tests automáticos; previsualizar con un servidor HTTP simple.

- Archivos clave:
  - [index.html](index.html) — estructura HTML y referencias a `styles.css` y `script.js`.
  - [script.js](script.js) — lógica principal: carga CSV, parseo, filtros, ordenación y render.
  - [data.csv](data.csv) — fuente de datos tabular consumida por el frontend.
  - [README.md](README.md) — contexto y notas del proyecto.

- Arquitectura "big picture":
  - Frontend estático: la lógica principal vive en `script.js` (referenciado desde `index.html`).
  - Flujo de datos: `script.js` hace `fetch('./data.csv')` → `csvToArray()` → `window.fullList` → `renderAllGenres()` → `printList()`.

- Esquema CSV observable (índices usados en el código):
  - `m[0]` — id numérico (usa para ordenar desc).
  - `m[2]` — fecha añadida (YYYY-MM-DD esperado).
  - `m[4]` — texto adicional / notas.
  - `m[5]` — título (UI y búsqueda).
  - `m[6]` — año (mostrado junto al título).
  - `m[7]` — URL IMDb (enlace en la fila).
  - `m[9]` — nota IMDb (mostrada en la columna de notas).
  - `m[12]` — géneros (coma-separados; parseado por `getGenreTags()`).
  - `m[16]` — "mi nota" (puede estar vacío).

Nota: los índices y campos están normalizados en la función `mapRowData()` — actualizar esa función si se añaden o reordenan columnas.

- Comportamientos importantes a preservar al editar:
  - `csvToArray()` usa una regex para campos citados; cualquier refactor debe conservar compatibilidad o incluir pruebas.
  - Tras parsear, `arrData` se limpia (`.filter(item => !!item[0])`) y se ordena por `id` (índice 0) de forma descendente.
  - `filterResults()` aplica debounce de 1000 ms y filtra por `title` (índice 5) y `year` (índice 6), comparando en minúsculas.
  - `printRow()` y `mapRowData()` son los puntos únicos de verdad para el render; si cambias columnas, actualiza ambos.

- Convenciones del proyecto y patrones observables:
  - Lógica principal en `script.js`. Mantener cambios localizados y compatibles con la API pública (window globals y query string `?json`).
  - Debounce manual en `filterResults()` (1000 ms). Evitar introducir debounce adicional sin evidencia de mejora UX.
  - `?json` en la query string hace que `printList()` devuelva `JSON.stringify(list)` (útil para integraciones con scripts).
  - La fecha "Actualizado" se obtiene consultando `Last-Modified` con `HEAD` sobre `data.csv` — requiere servir los archivos por HTTP.

- Flujo de desarrollo / comandos útiles:
  - Previsualizar localmente (recomendado):
    - `python -m http.server 8000` (desde la raíz del repo)
    - o `npx serve .`
  - Depuración: abrir DevTools, inspeccionar `window.fullList`, `window.filteredList`, `window.currentSort`.
  - Verificar cabeceras: `curl -I http://localhost:8000/data.csv` para comprobar `Last-Modified`.

- Sugerencias prácticas para cambios en CSV/renderizado:
  - Si se añaden columnas: actualizar `mapRowData()` y `printRow()`.
  - Si la columna de géneros cambia, actualizar `renderAllGenres()` y `getGenreTags()`.
  - Si cambias la ordenación por defecto, actualizar `window.currentSort` y documentarlo en el PR.
  - Mantener la ruta relativa `./data.csv` en las llamadas `fetch()` para compatibilidad local.

- Limitaciones detectadas:
  - Sin servidor HTTP, `fetch('./data.csv')` falla en navegadores; siempre probar con servidor local.
  - No hay tests ni CI configurados; los cambios en el parser CSV necesitan validación manual o la adición de tests.

---

Checklist rápido para PRs que toquen CSV o renderizado:
- Actualizar `mapRowData()` si se reordenan columnas.
- Adaptar `printRow()` para nuevas columnas visibles.
- Verificar `renderAllGenres()` si cambian los géneros.
- Probar localmente con `python -m http.server 8000` y comprobar `Last-Modified` con `curl -I`.

Si quieres, puedo transformar `csvToArray()` en un módulo testable y añadir pruebas unitarias.

Por favor revisa y dime si quieres añadir reglas de commit, plantilla para cambios en `data.csv`, o ejemplos de pruebas unitarias.

```# Instrucciones para agentes AI (Copilot)

Propósito: ayudar a agentes AI a ser productivos rápidamente en este repo estático.

- Resumen rápido:
  - Proyecto minimalista: sitio estático servido desde `index.html` que carga `data.csv` en el cliente.
  - No hay paso de build ni tests automáticos; previsualizar con un servidor HTTP simple.

- Archivos clave:
  - [index.html](index.html) — interfaz, parser CSV y lógica de filtrado/ordenación.
  - [data.csv](data.csv) — fuente de datos tabular consumida por el frontend.
  - [README.md](README.md) — contexto del proyecto (si existe).

- Arquitectura "big picture":
  - Frontend estático: toda la lógica de negocio está en `index.html` (JS inline).
  - Flujo de datos: `index.html` hace `fetch('data.csv')` → `csvToArray()` → `window.fullList`.
  - Visualización: `printList()` / `printRow()` renderizan filas en `#list`.

- Esquema CSV observable (índices usados en el código):
  - `m[0]` — id numérico (se usa para ordenar desc).
  - `m[2]` — fecha añadida (formato YYYY-MM-DD esperado).
  - `m[4]` — texto adicional / notas (opcional).
  - `m[5]` — título (usa en UI y en búsqueda).
  - `m[6]` — año (se muestra junto al título, también buscado).
  - `m[7]` — URL IMDb (enlace en la columna imdb).
  - `m[9]` — nota IMDb (mostrada en `col-notes`).
  - `m[12]` — géneros (coma-separados; `getGenreTags()` los parsea).
  - `m[16]` — "mi nota" (puede estar vacío).

- Comportamientos importantes a preservar al editar:
  - El parser `csvToArray()` usa una regex robusta para campos citados; mantener su lógica salvo refactor con tests.
  - Se filtra `arrData` para quitar filas sin `item[0]` y se ordena por `+a[0]` desc.
  - El filtrado en `filterResults()` compara `m[5]` y `m[6]` en minúsculas.
  - `printRow()` usa campos específicos (ver "Esquema CSV"). Si cambias columnas, actualiza todas las referencias.

- Convenciones del proyecto y patrones observables:
  - Lógica principal inline en `index.html`; preferir cambios pequeños y localizados.
  - Debounce manual en `filterResults()` con 1000 ms; no introduzcas otro debounce más agresivo sin justificar.
  - Respuesta JSON: si la query string es `?json`, `printList()` reemplaza `document.body.innerHTML` por `JSON.stringify(list)`.
  - Fecha de "Actualizado": se intenta obtener `Last-Modified` con una petición `HEAD` a `data.csv` — esto requiere servir el archivo por HTTP para funcionar.

- Flujo de desarrollo / comandos útiles:
  - Previsualizar localmente (recomendado):
    - `python -m http.server 8000` (desde la raíz del repo) o
    - `npx serve .` o cualquier servidor estático.
  - Depuración rápida en navegador: abrir DevTools y revisar `window.fullList` y `console`.
  - Para verificar la cabecera `Last-Modified`, usar `curl -I http://localhost:8000/data.csv`.

- Sugerencias para modificaciones por agentes AI:
  - Si agregas nuevas columnas al CSV: actualizar `printRow()`, `filterResults()` y la lista de índices del encabezado en este archivo.
  - Evitar romper la salida `?json` (útil para scripts). Si cambias su formato, documentarlo.
  - Mantener la ordenación por `m[0]` salvo que el equipo decida otro criterio; agregar una configuración explícita si se requiere.

- Limitaciones detectadas / notas prácticas:
  - Sin servidor HTTP, la petición `fetch('data.csv')` puede fallar por políticas de origen/archivo; siempre probar con un servidor.
  - No hay tests automatizados ni CI definidos en el repo actual.

Por favor revisa este archivo y dime si quieres que añada reglas de commit, una plantilla para cambios en el CSV, o ejemplos de pruebas unitarias para el parser CSV.
