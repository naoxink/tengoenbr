# tengoenbr

Sitio estático para gestionar un listado personal de películas/series. El
listado muestra un prefijo `#` que corresponde directamente a la línea del
CSV donde aparece el registro (1 = primera fila). Así evitamos lógica adicional
para calcular posiciones; la numeración se mantiene constante incluso si filtras
o reordenas. La tabla se carga inicialmente en el orden inverso del CSV, de
modo que las últimas filas del archivo aparecen primero; puedes cambiar el orden
mediante los controles si lo deseas.