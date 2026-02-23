#!/usr/bin/env python3
"""
update_rating.py
Actualizar la nota personal y la fecha de valoración para un ID concreto.
Uso:
  python update_rating.py 309 7.5            # set rating 7.5 and dateRated=TODAY
  python update_rating.py 309 7.5 --date 2026-01-01
  python update_rating.py 309 --clear       # borrar nota personal y fechaRated
  python update_rating.py 309 --dry-run
  python update_rating.py 309 --no-backup

Comportamiento:
- Actualiza todas las filas cuyo campo `id` (columna 0) coincide con el id solicitado.
- Escribe la nueva `Your Rating` en la columna 9 y `dateRated` en la columna 10.
- Por defecto `dateRated` se pone a la fecha actual (YYYY-MM-DD). Se puede pasar `--date` para fijar otra.
- Crea una copia de seguridad en `backups/` salvo si se pasa `--no-backup`.
"""

import argparse
import csv
import datetime
import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'data.csv')
NUM_COLS = 12

parser = argparse.ArgumentParser(description='Actualizar nota personal (Your Rating) y dateRated por id')
parser.add_argument('id', nargs='?', help='Const/IDIMDb a modificar')
parser.add_argument('rating', nargs='?', help='Nueva nota (ej: 7.5). Use --clear para borrar.')
parser.add_argument('--date', help='Fecha para dateRated (YYYY-MM-DD). Default: today')
parser.add_argument('--clear', action='store_true', help='Borrar la nota personal y la fechaRated')
parser.add_argument('--dry-run', action='store_true', help='Mostrar los cambios sin escribir')
parser.add_argument('--backup', action='store_true', help='(obsoleto) Crear copia de seguridad antes de escribir — ahora se crea automáticamente; usar --no-backup para evitar copia')
parser.add_argument('--no-backup', action='store_true', help='No crear copia de seguridad antes de escribir')
args = parser.parse_args()


def valid_date(s):
    try:
        datetime.datetime.strptime(s, '%Y-%m-%d')
        return True
    except Exception:
        return False


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


def prompt(msg, default=None, validator=None):
    while True:
        if default:
            val = input(f"{msg} [{default}]: ").strip()
            if val == '':
                val = default
        else:
            val = input(f"{msg}: ").strip()
        if validator:
            if validator(val):
                return val
            else:
                print('Valor no válido, inténtalo de nuevo.')
        else:
            return val


def parse_rating(s):
    if s is None or s == '':
        return ''
    try:
        v = float(str(s).replace(',', '.'))
        # allow values 0..10
        if v < 0 or v > 10:
            return None
        # keep original formatting with dot
        return str(v).rstrip('0').rstrip('.') if '.' in str(v) else str(int(v))
    except Exception:
        return None


def main():
    id_val = args.id
    if id_val is None:
        id_val = input('Const/IDIMDb a modificar: ').strip()
    if not id_val:
        print('ID inválido', file=sys.stderr)
        sys.exit(1)

    # Leer filas y preparar vista previa para confirmar título y nota actual
    rows_preview = read_rows(CSV_PATH)
    matches_preview = [r for r in rows_preview if len(r) > 0 and r[0] == str(id_val)]
    if len(matches_preview) == 0:
        print(f'No se encontró ningún registro con id {id_val}. Nada que hacer.')
        sys.exit(0)

    if args.clear:
        new_rating = ''
    else:
        if args.rating is None:
            # Mostrar título(s) y nota(s) actual(es) para confirmar
            if len(matches_preview) == 1:
                t = matches_preview[0][3] if len(matches_preview[0]) > 3 else ''  # título ahora en col 3
                cur = matches_preview[0][8] if len(matches_preview[0]) > 8 and matches_preview[0][8] != '' else 'Sin nota'
                prompt_text = f'Nueva nota personal para "{t}" (actual: {cur}) (ej: 7.5) (vacío para borrar)'
            else:
                # mostrar hasta 3 ejemplos si hay duplicados
                examples = []
                for m in matches_preview[:3]:
                    tt = m[3] if len(m) > 3 else ''
                    cr = m[8] if len(m) > 8 and m[8] != '' else 'Sin nota'
                    examples.append(f'"{tt}" ({cr})')
                prompt_text = f'{len(matches_preview)} coincidencias. Ej: ' + '; '.join(examples) + ' — Nueva nota (ej: 7.5) (vacío para borrar)'

            r = prompt(prompt_text, default='')
            if r == '':
                new_rating = ''
            else:
                parsed = parse_rating(r)
                if parsed is None:
                    print('Nota inválida. Debe ser numérica entre 0 y 10.', file=sys.stderr)
                    sys.exit(1)
                new_rating = parsed
        else:
            parsed = parse_rating(args.rating)
            if parsed is None:
                print('Nota inválida. Debe ser numérica entre 0 y 10.', file=sys.stderr)
                sys.exit(1)
            new_rating = parsed

    date_val = args.date
    if args.clear:
        new_date = ''
    else:
        if date_val:
            if not valid_date(date_val):
                print('Fecha inválida. Use formato YYYY-MM-DD.', file=sys.stderr)
                sys.exit(1)
            new_date = date_val
        else:
            new_date = datetime.date.today().isoformat()

    rows = read_rows(CSV_PATH)

    matched = []
    new_rows = []
    for r in rows:
        if len(r) == 0:
            new_rows.append(r)
            continue
        cur = r[0]
        if str(cur) == str(id_val):
            r_copy = list(r)
            # ensure length
            if len(r_copy) < NUM_COLS:
                r_copy += [''] * (NUM_COLS - len(r_copy))
            # columnas ajustadas al nuevo esquema:
            # 8 = Your Rating, 9 = Date Rated
            r_copy[8] = new_rating
            r_copy[9] = new_date
            new_rows.append(r_copy)
            matched.append((r, r_copy))
        else:
            new_rows.append(r)

    if len(matched) == 0:
        print(f'No se encontró ningún registro con id {id_val}. Nada que hacer.')
        sys.exit(0)

    if args.dry_run:
        print(f'DRY RUN: se actualizarían {len(matched)} fila(s) con id={id_val}.')
        from io import StringIO
        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(['--- Antes --->', '--- Después --->'])
        for before, after in matched[:20]:
            w.writerow(before)
            w.writerow(after)
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
    print(f'Actualizadas {len(matched)} fila(s) con id={id_val}.')


if __name__ == '__main__':
    main()
