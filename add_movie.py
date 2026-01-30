#!/usr/bin/env python3
"""
add_movie.py
Interactivo: añade una fila a data.csv siguiendo el esquema detectado en el repo.
Uso:
  python add_movie.py        # interactivo, añade al archivo
  python add_movie.py --dry-run  # muestra la fila CSV que se añadiría
  python add_movie.py --backup  # crea copia de seguridad antes de escribir

Mapa de columnas (nuevo, tras eliminar columnas 3,10,11,13,14,15):
 0: id
 1: Const (ID IMDb, ej: tt0133093)
 2: Created (fecha de inclusión)
 3: Additional Notes
 4: Title (título mostrado)
 5: Original Title
 6: IMDb URL
 7: Type (ej: Película)
 8: IMDb Rating
 9: Genres (coma-separados)
 10: Your Rating
 11: Fecha adicional / marcado (se usará fecha de hoy si no se proporciona)

Nota: el script calcula el siguiente id como max(id)+1.
"""

import argparse
import csv
import datetime
import shutil
import os
import re

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, 'data.csv')
NUM_COLS = 12

parser = argparse.ArgumentParser(description='Añadir película a data.csv')
parser.add_argument('--dry-run', action='store_true', help='Mostrar la fila CSV sin escribir')
parser.add_argument('--backup', action='store_true', help='(obsoleto) Crear copia de seguridad antes de escribir — ahora se crea automáticamente; usar --no-backup para evitar copia')
parser.add_argument('--no-backup', action='store_true', help='No crear copia de seguridad antes de escribir')
args = parser.parse_args()

def read_rows(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for r in reader:
            rows.append(r)
    return rows

def next_id(rows):
    max_id = 0
    for r in rows:
        if len(r) == 0:
            continue
        try:
            v = int(r[0])
            if v > max_id:
                max_id = v
        except Exception:
            continue
    return max_id + 1

def prompt(prompt_text, default=None, validator=None, optional=False):
    while True:
        if default:
            val = input(f"{prompt_text} [{default}]: ").strip()
            if val == '':
                val = default
        else:
            val = input(f"{prompt_text}: ").strip()
            if val == '' and optional:
                return ''
        if validator:
            if validator(val):
                return val
            else:
                print('Valor no válido, inténtalo de nuevo.')
        else:
            return val

def valid_date(s):
    try:
        datetime.datetime.strptime(s, '%Y-%m-%d')
        return True
    except Exception:
        return False

def valid_const(s):
    # imdb ttnnnnnnn or numeric allowed
    return bool(re.match(r'^(tt\d+)$', s)) or s == ''


def main():
    rows = read_rows(CSV_PATH)
    nid = next_id(rows)
    print(f'Nuevo id asignado: {nid}')

    title = prompt('Título (Title)', optional=False)
    created_def = datetime.date.today().isoformat()
    created = prompt('Fecha de inclusión (Created) formato YYYY-MM-DD', default=created_def, validator=valid_date)
    const = prompt('IDIMDb (Const) — ej: tt0133093 (dejar vacío si no aplica)', optional=True, validator=valid_const)
    original_title = prompt('Título original (Original Title) (opcional)', optional=True)
    imdb_rating = prompt('Puntuación IMDB (IMDb Rating) (opcional, ej: 7.3)', optional=True)
    genres = prompt('Géneros (separados por comas) (opcional)', optional=True)
    your_rating = prompt('Puntuación personal (Your Rating) (opcional)', optional=True)
    notes = prompt('Notas adicionales (opcional)', optional=True)

    imdb_url = ''
    if const:
        imdb_url = f'https://www.imdb.com/title/{const}/'

    # construir fila con NUM_COLS elementos (12 columnas tras el recorte)
    row = [''] * NUM_COLS
    row[0] = str(nid)
    row[1] = const
    row[2] = created
    row[3] = notes
    row[4] = title
    row[5] = original_title
    row[6] = imdb_url
    row[7] = 'Película'
    row[8] = imdb_rating
    row[9] = genres
    row[10] = your_rating
    row[11] = datetime.date.today().isoformat()

    if args.dry_run:
        # usar csv.writer para formatear correctamente (comillas, comas en campos)
        from io import StringIO
        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(row)
        line = buf.getvalue().strip('\n')
        print('\n--- DRY RUN: la fila que se añadiría a data.csv es: ---')
        print(line)
        return

    if not args.no_backup:
        BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
        os.makedirs(BACKUP_DIR, exist_ok=True)
        bname = f"data.csv.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        bpath = os.path.join(BACKUP_DIR, bname)
        shutil.copy(CSV_PATH, bpath)
        print(f'Copia de seguridad creada: {bpath}')

    # append
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)

    print('Fila añadida correctamente a', CSV_PATH)

if __name__ == '__main__':
    main()
