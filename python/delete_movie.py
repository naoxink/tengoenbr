#!/usr/bin/env python3
"""
delete_movie.py
Eliminar registro(s) por ID de IMDb (Const) en la columna 0.
Uso:
  python delete_movie.py tt0133093         # eliminar todas las filas que contengan ese Const
  python delete_movie.py tt0133093 --dry-run  # mostrar lo que cambiaría sin escribir
  python delete_movie.py tt0133093 --backup   # crea copia antes de escribir

Nota: ya no se reindexan filas, simplemente se borran las coincidencias.

Reglas:
- Si hay N filas con el ID solicitado, se eliminan todas ellas.
- Todos los registros con id > id_to_remove tendrán su id reducido en N (para mantener secuencia sin huecos).
- El archivo `data.csv` se toma relativo al script (misma carpeta).
"""

import argparse
import csv
import os
import shutil
import sys
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'data.csv')

parser = argparse.ArgumentParser(description='Eliminar registro(s) por id y reindexar siguientes IDs')
parser.add_argument('id', type=str, nargs='?', help='Const/IDIMDb (columna 0) a eliminar')
parser.add_argument('--dry-run', action='store_true', help='Mostrar los cambios sin escribir')
parser.add_argument('--backup', action='store_true', help='(obsoleto) Crear copia de seguridad antes de escribir — ahora se crea automáticamente; usar --no-backup para evitar copia')
parser.add_argument('--no-backup', action='store_true', help='No crear copia de seguridad antes de escribir')
args = parser.parse_args()


def read_rows(path):
    if not os.path.exists(path):
        print(f'ERROR: {path} no encontrado.', file=sys.stderr)
        sys.exit(1)
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for r in reader:
            rows.append(r)
    return rows


def write_rows(path, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main():
    id_to_remove = args.id
    if id_to_remove is None:
        id_to_remove = input('Const (IDIMDb) a eliminar: ').strip()
        if not id_to_remove:
            print('ID inválido', file=sys.stderr)
            sys.exit(1)

    rows = read_rows(CSV_PATH)

    # count rows that match the provided Const
    removed_rows = [r for r in rows if len(r) > 0 and r[0] == id_to_remove]
    num_removed = len(removed_rows)

    if num_removed == 0:
        print(f'No se encontró ningún registro con Const {id_to_remove}. Nada que hacer.')
        sys.exit(0)

    # Build new rows: simply drop any row whose first col equals the value
    new_rows = [r for r in rows if not (len(r) > 0 and r[0] == id_to_remove)]
    updated_count = 0  # no renumeración

    if args.dry_run:
        print(f'DRY RUN: eliminaría {num_removed} fila(s) con Const={id_to_remove}.')
        print('\n--- Preview de primeras filas tras eliminación ---')
        from io import StringIO
        buf = StringIO()
        w = csv.writer(buf)
        for r in new_rows[:20]:
            w.writerow(r)
        print(buf.getvalue())
        return

    if not args.no_backup:
        BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
        os.makedirs(BACKUP_DIR, exist_ok=True)
        bname = f"data.csv.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        bpath = os.path.join(BACKUP_DIR, bname)
        shutil.copy(CSV_PATH, bpath)
        print(f'Copia de seguridad creada: {bpath}')

    write_rows(CSV_PATH, new_rows)
    print(f'Eliminadas {num_removed} fila(s) con Const={id_to_remove}.')


if __name__ == '__main__':
    main()
