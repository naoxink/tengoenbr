#!/usr/bin/env python3
"""
add_movie.py
Interactivo: añade una fila a data.csv siguiendo el esquema detectado en el repo.
Uso:
  python add_movie.py        # interactivo, añade al archivo
  python add_movie.py --dry-run  # muestra la fila CSV que se añadiría
  python add_movie.py --backup  # crea copia de seguridad antes de escribir

Mapa de columnas (nuevo, tras eliminar la columna "Position" y otras anteriores):
 0: Const (ID IMDb, ej: tt0133093)
 1: Created (fecha de inclusión)
 2: Additional Notes
 3: Title (título mostrado)
 4: Original Title
 5: IMDb URL
 6: Type (ej: Película)
 7: Genres (coma-separados)
 8: Your Rating
 9: Date Rated (se usará fecha de hoy si no se proporciona)
 10: Formato

Nota: el script ya no genera ni mantiene un ID numérico; simplemente
construye la fila en el orden de columnas arriba.
"""

import argparse
import csv
import datetime
import shutil
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'data.csv')
NUM_COLS = 11

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

# la columna de identificador numérico ya no existe en el CSV, así que
# esta función quedaba obsoleta y se conserva solo por compatibilidad
# histórica (no se utiliza).

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
    # no se asigna id numérico; la primera columna es el Const proporcionado

    title = prompt('Título (Title)', optional=False)
    created_def = ''
    # la fecha de inclusión ahora es opcional; aceptar línea vacía
    created = prompt('Fecha de inclusión (Created) formato YYYY-MM-DD (opcional)', default=created_def, validator=lambda s: valid_date(s) or s=='')
    const = prompt('IDIMDb (Const) — ej: tt0133093 (opcional)', optional=True, validator=valid_const)
    original_title = prompt('Título original (Original Title) (opcional)', optional=True)
    type = prompt('Tipo (Película o Serie) (Película por defecto)', optional=True) or 'Película'
    genres = prompt('Géneros (separados por comas) (opcional)', optional=True)
    your_rating = prompt('Puntuación personal (Your Rating) (opcional)', optional=True)
    notes = prompt('Notas adicionales (opcional)', optional=True)
    formato = prompt('Formato (br o dvd)', optional=True)

    imdb_url = ''
    if const:
        imdb_url = f'https://www.imdb.com/title/{const}/'

    # construir fila con NUM_COLS elementos (11 columnas tras eliminar la columna "Position")
    row = [''] * NUM_COLS
    row[0] = const
    row[1] = created
    row[2] = notes
    row[3] = title
    row[4] = original_title
    row[5] = imdb_url
    row[6] = type
    row[7] = genres
    row[8] = your_rating
    row[9] = datetime.date.today().isoformat()
    row[10] = formato

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

    # append (constante primero)
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)

    print('Fila añadida correctamente a', CSV_PATH)

if __name__ == '__main__':
    main()
