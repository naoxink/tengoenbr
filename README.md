# tengoenbr

Sitio estático para gestionar un listado personal de películas/series. El
listado muestra un prefijo `#` que corresponde directamente a la línea del
CSV donde aparece el registro (1 = primera fila). Así evitamos lógica adicional
para calcular posiciones; la numeración se mantiene constante incluso si filtras
o reordenas. La tabla se carga inicialmente en el orden inverso del CSV, de
modo que las últimas filas del archivo aparecen primero; puedes cambiar el orden
mediante los controles si lo deseas (la opción "Orden CSV" restaura esa secuencia).

La fecha de inclusión es opcional: si falta, el listado muestra un `?` en lugar de
la fecha.

Los registros contienen una columna adicional para el tipo de título (`Película`, `Serie`, etc.) que se muestra como una etiqueta breve junto al título en la tabla. El título original (si difiere del principal) se muestra en una línea secundaria y en un color discreto para evitar que las filas queden demasiado largas.

En la sección de filtros puedes elegir el **tipo** para restringir la lista a películas o series; selecciona "Todos" para quitar el filtro.