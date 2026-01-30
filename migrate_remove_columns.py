#!/usr/bin/env python3
"""
migrate_remove_columns.py
Migración del CSV eliminando las columnas (por índice): 3, 10, 11, 13, 14, 15
- Crea un backup en backups/ (timestamped)
- Soporta --dry-run para mostrar sample sin escribir
- No requiere dependencias externas
"""

import csv
import os
import shutil
import datetime
import argparse
import sys

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, 'data.csv')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
REMOVE_INDICES = [3,10,11,13,14,15]

parser = argparse.ArgumentParser(description='Eliminar columnas específicas de data.csv (migration)')
parser.add_argument('--dry-run', action='store_true', help='No escribir, solo mostrar resumen')
args = parser.parse_args()


def read_rows(path):
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


def transform_row(r):
    # Remove by original indices; safer to build new list keeping indices not in REMOVE_INDICES
    new = []
    for i, v in enumerate(r):
        if i in REMOVE_INDICES:
            continue
        new.append(v)
    return new


def main():
    if not os.path.exists(CSV_PATH):
        print('ERROR: data.csv not found.', file=sys.stderr)
        sys.exit(1)

    rows = read_rows(CSV_PATH)
    new_rows = [transform_row(r) for r in rows]

    # quick checks: confirm all rows length consistent
    lengths = set(len(r) for r in new_rows)
    print(f'Procesadas {len(rows)} filas; longitudes resultantes: {sorted(lengths)}')
    if args.dry_run:
        print('\nEjemplo (primeras 3 filas tras transformación):')
        for r in new_rows[:3]:
            print(','.join([f'"{c}"' if (',' in c or '"' in c or '\n' in c) else c for c in r]))
        return

    # create backup
    os.makedirs(BACKUP_DIR, exist_ok=True)
    bname = f"data.csv.pre_migrate.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    bpath = os.path.join(BACKUP_DIR, bname)
    shutil.copy(CSV_PATH, bpath)
    print(f'Backup creado: {bpath}')

    write_rows(CSV_PATH, new_rows)
    print('data.csv reescrito con las columnas eliminadas.')

if __name__ == '__main__':
    main()
