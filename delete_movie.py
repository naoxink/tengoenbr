#!/usr/bin/env python3
"""
delete_movie.py
Eliminar registro(s) por ID (columna 0) y ajustar los IDs siguientes para evitar saltos.
Uso:
  python delete_movie.py 309         # eliminar id 309 (modifica data.csv)
  python delete_movie.py 309 --dry-run  # mostrar lo que cambiaría sin escribir
  python delete_movie.py 309 --backup   # crea copia antes de escribir

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

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, 'data.csv')

parser = argparse.ArgumentParser(description='Eliminar registro(s) por id y reindexar siguientes IDs')
parser.add_argument('id', type=int, nargs='?', help='ID (columna 0) a eliminar')
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
        try:
            id_to_remove = int(input('ID a eliminar: ').strip())
        except Exception:
            print('ID inválido', file=sys.stderr)
            sys.exit(1)

    rows = read_rows(CSV_PATH)

    # count rows that match id_to_remove
    removed_rows = [r for r in rows if len(r) > 0 and r[0].isdigit() and int(r[0]) == id_to_remove]
    num_removed = len(removed_rows)

    if num_removed == 0:
        print(f'No se encontró ningún registro con id {id_to_remove}. Nada que hacer.')
        sys.exit(0)

    # Build new rows: remove matching, decrement ids > id_to_remove by num_removed
    new_rows = []
    updated_count = 0
    for r in rows:
        if len(r) == 0:
            new_rows.append(r)
            continue
        try:
            cur_id = int(r[0])
        except Exception:
            # If first column is not numeric, leave row as-is
            new_rows.append(r)
            continue
        if cur_id == id_to_remove:
            # skip (remove)
            continue
        if cur_id > id_to_remove:
            new_id = cur_id - num_removed
            r_copy = list(r)
            r_copy[0] = str(new_id)
            new_rows.append(r_copy)
            updated_count += 1
        else:
            new_rows.append(r)

    if args.dry_run:
        print(f'DRY RUN: {num_removed} fila(s) eliminaría con id={id_to_remove}.')
        print(f'DRY RUN: {updated_count} fila(s) tendrían su id decrementado en {num_removed}.')
        # print a preview (first few modified rows)
        print('\n--- Preview de filas modificadas / agregadas ---')
        # show top 10 rows of resulting file for quick check
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
    print(f'Eliminadas {num_removed} fila(s) con id={id_to_remove}. Se actualizaron {updated_count} fila(s).')


if __name__ == '__main__':
    main()
