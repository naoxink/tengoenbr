#!/usr/bin/env python3
"""
manage_backups.py
Herramienta ligera para listar, inspeccionar, restaurar y comparar backups en `backups/`.
Uso:
  python manage_backups.py list
  python manage_backups.py show <name|index>
  python manage_backups.py diff <name|index> [other_name|other_index]
  python manage_backups.py restore <name|index> [--yes] [--backup]
  python manage_backups.py delete <name|index> [--yes]

Todo nativo (sin dependencias externas).
"""

import argparse
import os
import sys
import datetime
import shutil
import difflib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / 'backups'
DATA_CSV = BASE_DIR / 'data.csv'


def human_readable_size(num):
    """Convert bytes to a human-readable string (e.g., 1.2 MB)."""
    num = float(num)
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0 or unit == 'TB':
            if unit == 'bytes':
                return f"{int(num)} {unit}"
            return f"{num:.1f} {unit}"
        num /= 1024.0


def list_backups():
    if not BACKUP_DIR.exists():
        print('No hay backups (carpeta backups/ no existe).')
        return []
    files = sorted(BACKUP_DIR.iterdir(), key=lambda p: p.stat().st_mtime)
    out = []
    for i, p in enumerate(files, start=1):
        st = p.stat()
        mtime = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        size = human_readable_size(st.st_size)
        print(f'{i:3d}. {p.name} — {mtime} — {size}')
        out.append(p)
    return out


def resolve_arg(arg):
    # accept index (1-based) or filename
    files = sorted(BACKUP_DIR.iterdir(), key=lambda p: p.stat().st_mtime) if BACKUP_DIR.exists() else []
    if arg.isdigit():
        i = int(arg)
        if 1 <= i <= len(files):
            return files[i-1]
        else:
            raise SystemExit(f'Índice fuera de rango: {arg}')
    p = BACKUP_DIR / arg
    if p.exists():
        return p
    raise SystemExit(f'Backup no encontrado: {arg}')


def show_file(p):
    print(f'--- {p} ---')
    with p.open(encoding='utf-8') as f:
        for ln in f:
            print(ln.rstrip())


RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
GRAY = "\033[90m"
RESET = "\033[0m"

def diff_files(file1, file2):
    with open(file1) as f1, open(file2) as f2:
        diff = difflib.unified_diff(
            f1.readlines(),
            f2.readlines()
        )

        for line in diff:
            if line.startswith("@@"):
                print(CYAN + line + RESET, end="")
                print()  # separación visual del bloque

            elif line.startswith("+++ ") or line.startswith("--- "):
                print(GRAY + line + RESET, end="")

            elif line.startswith("+"):
                print(GREEN + line + RESET, end="")

            elif line.startswith("-"):
                print(RED + line + RESET, end="")

            else:
                print(line, end="")


def restore(p, yes=False, do_backup=False):
    if not p.exists():
        raise SystemExit('Backup no encontrado')
    if do_backup:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        bname = f"data.csv.pre_restore.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        bpath = BACKUP_DIR / bname
        shutil.copy(DATA_CSV, bpath)
        print(f'Copia previa creada: {bpath}')
    if not yes:
        confirm = input(f'Restaurar {p.name} en {DATA_CSV}? (y/N): ').strip().lower()
        if confirm != 'y':
            print('Operación cancelada.')
            return
    shutil.copy(p, DATA_CSV)
    print(f'Restaurado {p.name} → {DATA_CSV}')


def delete_backup(p, yes=False):
    if not p.exists():
        raise SystemExit('Backup no encontrado')
    if not yes:
        confirm = input(f'Borrar backup {p.name}? (y/N): ').strip().lower()
        if confirm != 'y':
            print('Operación cancelada.')
            return
    p.unlink()
    print(f'Backup eliminado: {p.name}')


def main():
    parser = argparse.ArgumentParser(description='Gestor de backups en backups/')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('list', help='Listar backups')

    pshow = sub.add_parser('show', help='Mostrar contenido de un backup (por nombre o índice)')
    pshow.add_argument('which')

    pdiff = sub.add_parser('diff', help='Mostrar diff entre backups o backup vs data.csv')
    pdiff.add_argument('a')
    pdiff.add_argument('b', nargs='?')

    prest = sub.add_parser('restore', help='Restaurar backup a data.csv')
    prest.add_argument('which')
    prest.add_argument('--yes', '-y', action='store_true', help='Confirmar sin preguntar')
    prest.add_argument('--backup', action='store_true', help='Hacer backup previo de data.csv en backups/')

    pdel = sub.add_parser('delete', help='Borrar backup')
    pdel.add_argument('which')
    pdel.add_argument('--yes', '-y', action='store_true')

    args = parser.parse_args()
    if args.cmd == 'list':
        list_backups()
        return
    if args.cmd == 'show':
        p = resolve_arg(args.which)
        show_file(p)
        return
    if args.cmd == 'diff':
        a = resolve_arg(args.a)
        if args.b:
            b = resolve_arg(args.b)
        else:
            b = DATA_CSV
            if not b.exists():
                raise SystemExit('No existe data.csv para comparar')
        diff_files(a, b)
        return
    if args.cmd == 'restore':
        p = resolve_arg(args.which)
        restore(p, yes=args.yes, do_backup=args.backup)
        return
    if args.cmd == 'delete':
        p = resolve_arg(args.which)
        delete_backup(p, yes=args.yes)
        return
    parser.print_help()

if __name__ == '__main__':
    main()
