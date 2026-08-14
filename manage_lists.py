#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manage_lists.py
================
Gestión por menú (terminal) de los listados de tengoenbr:

  - data.json         -> Colección (películas/series que ya tienes)
  - paracomprar.json  -> Para comprar (las quieres en bluray, no las tienes)
  - misnotas.json     -> Vistas sin comprar (las has visto, apuntas tu nota)

Antes de escribir en cualquiera de los tres ficheros se crea automáticamente
un backup en backups/<dataset>/<fichero>_<timestamp>.json.

Uso:
    python manage_lists.py
"""

import json
import os
import shutil
import sys
import difflib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

# ---------------------------------------------------------------------------
# Definición de los datasets: fichero + esquema de campos
# ---------------------------------------------------------------------------
# Tipos soportados: str, float, int, bool, list, date
# 'required' -> obligatorio al añadir
# 'clear_kw' -> palabra especial para vaciar el campo al editar (por defecto "-")

FIELD_TYPES_HELP = {
    "str": "texto libre",
    "float": "número decimal (ej. 9.95)",
    "int": "número entero",
    "bool": "s/n",
    "list": "lista separada por comas (ej. Acción, Crimen)",
    "date": "fecha AAAA-MM-DD (ej. 2026-08-14)",
}

DATASETS = {
    "coleccion": {
        "label": "Colección",
        "file": "data.json",
        "fields": [
            {"key": "id", "label": "ID IMDb (const)", "type": "str", "required": True},
            {"key": "title", "label": "Título", "type": "str", "required": True},
            {"key": "original_title", "label": "Título original", "type": "str", "required": False},
            {"key": "url", "label": "URL IMDb", "type": "str", "required": False},
            {"key": "type", "label": "Tipo (Película/Serie/MiniSerie)", "type": "str", "required": False},
            {"key": "genres", "label": "Géneros", "type": "list", "required": False},
            {"key": "created", "label": "Fecha de inclusión", "type": "date", "required": False},
            {"key": "store", "label": "Tienda de compra", "type": "str", "required": False},
            {"key": "price", "label": "Precio", "type": "float", "required": False},
            {"key": "gift", "label": "¿Es un regalo?", "type": "bool", "required": False},
            {"key": "rating", "label": "Tu nota", "type": "float", "required": False},
            {"key": "date_rated", "label": "Fecha en que valoraste", "type": "date", "required": False},
            {"key": "format", "label": "Formato (bluray/dvd/br)", "type": "str", "required": False},
        ],
    },
    "comprar": {
        "label": "Para comprar",
        "file": "paracomprar.json",
        "fields": [
            {"key": "id", "label": "ID IMDb (const)", "type": "str", "required": True},
            {"key": "title", "label": "Título", "type": "str", "required": True},
            {"key": "original_title", "label": "Título original", "type": "str", "required": False},
            {"key": "url", "label": "URL IMDb", "type": "str", "required": False},
            {"key": "type", "label": "Tipo (Película/Serie/MiniSerie)", "type": "str", "required": False},
            {"key": "genres", "label": "Géneros", "type": "list", "required": False},
            {"key": "created", "label": "Fecha en que la añadiste a la lista", "type": "date", "required": False},
            {"key": "priority", "label": "Prioridad (alta/media/baja)", "type": "str", "required": False},
            {"key": "notes", "label": "Notas", "type": "str", "required": False},
        ],
    },
    "vistas": {
        "label": "Vistas sin comprar",
        "file": "misnotas.json",
        "fields": [
            {"key": "id", "label": "ID IMDb (const)", "type": "str", "required": True},
            {"key": "title", "label": "Título", "type": "str", "required": True},
            {"key": "original_title", "label": "Título original", "type": "str", "required": False},
            {"key": "url", "label": "URL IMDb", "type": "str", "required": False},
            {"key": "type", "label": "Tipo (Película/Serie/MiniSerie)", "type": "str", "required": False},
            {"key": "genres", "label": "Géneros", "type": "list", "required": False},
            {"key": "created", "label": "Fecha en que la añadiste a la lista", "type": "date", "required": False},
            {"key": "rating", "label": "Tu nota", "type": "float", "required": False},
            {"key": "date_rated", "label": "Fecha en que valoraste", "type": "date", "required": False},
        ],
    },
}

CLEAR_KEYWORD = "-"  # escribir esto en un campo al editar lo deja vacío/null


# ---------------------------------------------------------------------------
# Utilidades de E/S
# ---------------------------------------------------------------------------

def data_path(ds_key):
    return os.path.join(BASE_DIR, DATASETS[ds_key]["file"])


def load_data(ds_key):
    path = data_path(ds_key)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  {DATASETS[ds_key]['file']} no es un JSON válido. Se trata como lista vacía.")
            return []


def save_data(ds_key, data):
    backup(ds_key)
    path = data_path(ds_key)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")
    print(f"✅ Guardado en {DATASETS[ds_key]['file']} ({len(data)} elementos).")


def backup(ds_key):
    """Crea un backup con timestamp del fichero actual (si existe) antes de tocarlo."""
    src = data_path(ds_key)
    if not os.path.exists(src):
        return None
    ds_backup_dir = os.path.join(BACKUPS_DIR, ds_key)
    os.makedirs(ds_backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATASETS[ds_key]["file"]
    name, ext = os.path.splitext(filename)
    dest = os.path.join(ds_backup_dir, f"{name}_{stamp}{ext}")
    shutil.copy2(src, dest)
    print(f"🗂️  Backup creado: {os.path.relpath(dest, BASE_DIR)}")
    return dest


def list_backups(ds_key):
    ds_backup_dir = os.path.join(BACKUPS_DIR, ds_key)
    if not os.path.isdir(ds_backup_dir):
        return []
    files = [f for f in os.listdir(ds_backup_dir) if f.endswith(".json")]
    files.sort(reverse=True)  # más recientes primero
    return files


# ---------------------------------------------------------------------------
# Entrada de datos por consola
# ---------------------------------------------------------------------------

def prompt_value(field, current=None, editing=False):
    label = field["label"]
    ftype = field["type"]
    hint = FIELD_TYPES_HELP[ftype]

    if editing:
        shown = current
        if ftype == "list" and isinstance(current, list):
            shown = ", ".join(current)
        prompt = f"  {label} [{hint}] (actual: {shown!r}, Enter=mantener, '{CLEAR_KEYWORD}'=vaciar): "
    else:
        req = " (obligatorio)" if field.get("required") else " (Enter=vacío)"
        prompt = f"  {label} [{hint}]{req}: "

    raw = input(prompt).strip()

    if editing and raw == "":
        return current, False  # sin cambios
    if raw == CLEAR_KEYWORD:
        return (None if ftype != "list" else []), True

    if raw == "" and not editing:
        if field.get("required"):
            print("    ⚠️  Este campo es obligatorio.")
            return prompt_value(field, current, editing)
        return (None if ftype != "list" else []), True

    try:
        value = cast_value(raw, ftype)
    except ValueError:
        print(f"    ⚠️  Valor no válido para tipo {ftype}. Inténtalo de nuevo.")
        return prompt_value(field, current, editing)

    return value, True


def cast_value(raw, ftype):
    if ftype == "str":
        return raw
    if ftype == "float":
        return float(raw.replace(",", "."))
    if ftype == "int":
        return int(raw)
    if ftype == "bool":
        return raw.lower() in ("s", "si", "sí", "y", "yes", "true", "1")
    if ftype == "list":
        return [x.strip() for x in raw.split(",") if x.strip()]
    if ftype == "date":
        datetime.strptime(raw, "%Y-%m-%d")  # valida formato
        return raw
    return raw


# ---------------------------------------------------------------------------
# Operaciones sobre un dataset
# ---------------------------------------------------------------------------

def summarize_item(ds_key, item):
    ftype = DATASETS[ds_key]["file"]
    bits = [item.get("id", "?"), item.get("title", "(sin título)")]
    if "rating" in item and item.get("rating") is not None:
        bits.append(f"nota:{item['rating']}")
    if "priority" in item and item.get("priority"):
        bits.append(f"prioridad:{item['priority']}")
    return " | ".join(str(b) for b in bits)


def cmd_list(ds_key):
    data = load_data(ds_key)
    if not data:
        print("(lista vacía)")
        return
    page_size = 20
    i = 0
    while i < len(data):
        chunk = data[i:i + page_size]
        for idx, item in enumerate(chunk, start=i + 1):
            print(f"{idx:>4}. {summarize_item(ds_key, item)}")
        i += page_size
        if i < len(data):
            cont = input(f"-- {i}/{len(data)} mostrados. Enter para seguir, 'q' para parar -- ").strip().lower()
            if cont == "q":
                break
    print(f"Total: {len(data)} elementos.")


def cmd_search(ds_key):
    data = load_data(ds_key)
    term = input("Buscar (título contiene): ").strip().lower()
    if not term:
        return []
    matches = [
        (i, item) for i, item in enumerate(data)
        if term in (item.get("title") or "").lower()
        or term in (item.get("original_title") or "").lower()
        or term == (item.get("id") or "").lower()
    ]
    if not matches:
        print("Sin resultados.")
    else:
        for i, item in matches:
            print(f"{i:>4}. {summarize_item(ds_key, item)}")
    return matches


def cmd_add(ds_key):
    data = load_data(ds_key)
    fields = DATASETS[ds_key]["fields"]
    print(f"\nAñadir a «{DATASETS[ds_key]['label']}» (Ctrl+C para cancelar)\n")

    new_id = None
    item = {}
    try:
        for field in fields:
            value, _ = prompt_value(field, editing=False)
            item[field["key"]] = value
            if field["key"] == "id":
                new_id = value
    except KeyboardInterrupt:
        print("\nCancelado.")
        return

    if new_id and any((existing.get("id") == new_id) for existing in data):
        confirm = input(f"⚠️  Ya existe un elemento con id {new_id!r}. ¿Añadir de todos modos? (s/N): ").strip().lower()
        if confirm != "s":
            print("Cancelado.")
            return

    data.append(item)
    save_data(ds_key, data)


def select_item(ds_key):
    """Busca y deja elegir un elemento; devuelve (index, item) o (None, None)."""
    matches = cmd_search(ds_key)
    if not matches:
        return None, None
    if len(matches) == 1:
        return matches[0]
    choice = input("Nº de línea a seleccionar (Enter para cancelar): ").strip()
    if not choice:
        return None, None
    try:
        idx = int(choice)
    except ValueError:
        print("Valor no válido.")
        return None, None
    data = load_data(ds_key)
    for i, item in matches:
        if i == idx:
            return i, item
    print("Ese número no está entre los resultados de la búsqueda.")
    return None, None


def cmd_edit(ds_key):
    idx, item = select_item(ds_key)
    if item is None:
        return
    fields = DATASETS[ds_key]["fields"]
    print(f"\nEditando: {summarize_item(ds_key, item)}")
    print("(Enter = mantener el valor actual, '-' = vaciar el campo)\n")

    data = load_data(ds_key)
    updated = dict(item)
    try:
        for field in fields:
            if field["key"] == "id":
                # el id no se edita para no romper referencias; hay que borrar+crear
                continue
            current = updated.get(field["key"])
            value, changed = prompt_value(field, current=current, editing=True)
            if changed:
                updated[field["key"]] = value
    except KeyboardInterrupt:
        print("\nCancelado.")
        return

    data[idx] = updated
    save_data(ds_key, data)


def cmd_delete(ds_key):
    idx, item = select_item(ds_key)
    if item is None:
        return
    print(f"\nVas a eliminar: {summarize_item(ds_key, item)}")
    confirm = input("¿Confirmas? (s/N): ").strip().lower()
    if confirm != "s":
        print("Cancelado.")
        return
    data = load_data(ds_key)
    del data[idx]
    save_data(ds_key, data)


# ---------------------------------------------------------------------------
# Gestión de backups
# ---------------------------------------------------------------------------

def backups_menu():
    while True:
        print("\n--- Gestionar backups ---")
        for key, ds in DATASETS.items():
            print(f"  {key}: {ds['label']} ({ds['file']})")
        ds_key = input("¿De qué dataset? (nombre de arriba, Enter=volver): ").strip().lower()
        if not ds_key:
            return
        if ds_key not in DATASETS:
            print("Dataset no reconocido.")
            continue
        backups_submenu(ds_key)


def backups_submenu(ds_key):
    while True:
        files = list_backups(ds_key)
        print(f"\n--- Backups de {DATASETS[ds_key]['label']} ({len(files)}) ---")
        for i, f in enumerate(files):
            print(f"  {i}. {f}")
        print("  1) Ver contenido de un backup")
        print("  2) Comparar backup vs fichero actual")
        print("  3) Restaurar un backup")
        print("  4) Eliminar un backup")
        print("  0) Volver")
        choice = input("> ").strip()

        if choice == "0" or choice == "":
            return
        elif choice == "1":
            b = pick_backup(files)
            if b:
                show_backup(ds_key, b)
        elif choice == "2":
            b = pick_backup(files)
            if b:
                diff_backup(ds_key, b)
        elif choice == "3":
            b = pick_backup(files)
            if b:
                restore_backup(ds_key, b)
        elif choice == "4":
            b = pick_backup(files)
            if b:
                delete_backup(ds_key, b)
        else:
            print("Opción no reconocida.")


def pick_backup(files):
    if not files:
        print("No hay backups todavía.")
        return None
    choice = input("Número de backup (Enter=cancelar): ").strip()
    if not choice:
        return None
    try:
        idx = int(choice)
        return files[idx]
    except (ValueError, IndexError):
        print("Número no válido.")
        return None


def backup_path(ds_key, filename):
    return os.path.join(BACKUPS_DIR, ds_key, filename)


def show_backup(ds_key, filename):
    path = backup_path(ds_key, filename)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"\n{filename} — {len(data)} elementos:")
    for i, item in enumerate(data[:30]):
        print(f"{i:>4}. {summarize_item(ds_key, item)}")
    if len(data) > 30:
        print(f"... y {len(data) - 30} más.")


def diff_backup(ds_key, filename):
    backup_file = backup_path(ds_key, filename)
    current_file = data_path(ds_key)
    with open(backup_file, "r", encoding="utf-8") as f:
        backup_lines = f.readlines()
    if os.path.exists(current_file):
        with open(current_file, "r", encoding="utf-8") as f:
            current_lines = f.readlines()
    else:
        current_lines = []
    diff = difflib.unified_diff(
        backup_lines, current_lines,
        fromfile=f"backup:{filename}", tofile=f"actual:{DATASETS[ds_key]['file']}",
        lineterm=""
    )
    printed = False
    for line in diff:
        print(line)
        printed = True
    if not printed:
        print("Sin diferencias.")


def restore_backup(ds_key, filename):
    confirm = input(f"Vas a sustituir {DATASETS[ds_key]['file']} por {filename}. "
                     "Se hará backup del estado actual antes. ¿Confirmas? (s/N): ").strip().lower()
    if confirm != "s":
        print("Cancelado.")
        return
    backup(ds_key)  # backup del estado actual antes de sobrescribir
    src = backup_path(ds_key, filename)
    dest = data_path(ds_key)
    shutil.copy2(src, dest)
    print(f"✅ Restaurado {DATASETS[ds_key]['file']} desde {filename}.")


def delete_backup(ds_key, filename):
    confirm = input(f"¿Eliminar el backup {filename}? Esto no afecta al fichero actual. (s/N): ").strip().lower()
    if confirm != "s":
        print("Cancelado.")
        return
    os.remove(backup_path(ds_key, filename))
    print("🗑️  Backup eliminado.")


# ---------------------------------------------------------------------------
# Menús
# ---------------------------------------------------------------------------

def dataset_menu(ds_key):
    ds = DATASETS[ds_key]
    while True:
        count = len(load_data(ds_key))
        print(f"\n--- {ds['label']} ({ds['file']}) — {count} elementos ---")
        print("  1) Listar")
        print("  2) Buscar")
        print("  3) Añadir")
        print("  4) Editar")
        print("  5) Eliminar")
        print("  0) Volver al menú principal")
        choice = input("> ").strip()

        if choice == "0" or choice == "":
            return
        elif choice == "1":
            cmd_list(ds_key)
        elif choice == "2":
            cmd_search(ds_key)
        elif choice == "3":
            cmd_add(ds_key)
        elif choice == "4":
            cmd_edit(ds_key)
        elif choice == "5":
            cmd_delete(ds_key)
        else:
            print("Opción no reconocida.")


def main_menu():
    while True:
        print("\n================ tengoenbr — gestión de listados ================")
        print("  1) Colección          (data.json)")
        print("  2) Para comprar        (paracomprar.json)")
        print("  3) Vistas sin comprar  (misnotas.json)")
        print("  4) Gestionar backups")
        print("  0) Salir")
        choice = input("> ").strip()

        if choice == "0":
            print("Hasta luego 👋")
            sys.exit(0)
        elif choice == "1":
            dataset_menu("coleccion")
        elif choice == "2":
            dataset_menu("comprar")
        elif choice == "3":
            dataset_menu("vistas")
        elif choice == "4":
            backups_menu()
        else:
            print("Opción no reconocida.")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nHasta luego 👋")
        sys.exit(0)