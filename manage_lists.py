#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manage_lists.py
================
Gestión por menú (terminal) de los listados de tengoenbr:

  - data.json         -> Colección (películas/series que ya tienes)
  - paracomprar.json  -> Para comprar (las quieres en bluray, no las tienes)

Antes de escribir en cualquiera de los dos ficheros se crea automáticamente
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
import tmdb_lookup

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
            {"key": "format", "label": "Formato (dvd/br)", "type": "str", "required": False},
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

STORES = ["ECI", "CEX", "Fnac", "Amazon", "Game", "MediaMarkt"]


def today():
    return datetime.now().strftime("%Y-%m-%d")


def field_defaults(ds_key, item):
    """Valores por defecto (Enter = aceptar) según el dataset y lo ya rellenado."""
    d = {"created": today()}
    if ds_key == "coleccion":
        d["format"] = "br"
    elif ds_key == "comprar":
        d["priority"] = "media"
    if item.get("rating") is not None:
        d["date_rated"] = today()
    return d


def prompt_store():
    """Devuelve (store, gift)."""
    print("  Tienda:")
    for i, s in enumerate(STORES, 1):
        print(f"    {i}. {s}")
    print("    0. Otra (escribir)   r. Regalo   Enter. Sin dato")
    while True:
        ch = input("  > ").strip().lower()
        if ch == "":
            return None, False
        if ch == "r":
            return None, True
        if ch == "0":
            name = input("  Nombre de la tienda: ").strip()
            return (name or None), False
        if ch.isdigit() and 1 <= int(ch) <= len(STORES):
            return STORES[int(ch) - 1], False
        match = next((s for s in STORES if s.lower() == ch), None)
        if match:
            return match, False
        print("    ⚠️  Opción no válida.")

def prompt_value(field, current=None, editing=False, default=None):
    label = field["label"]
    ftype = field["type"]
    hint = FIELD_TYPES_HELP[ftype]

    if editing:
        shown = current
        if ftype == "list" and isinstance(current, list):
            shown = ", ".join(current)
        prompt = f"  {label} [{hint}] (actual: {shown!r}, Enter=mantener, '{CLEAR_KEYWORD}'=vaciar): "
    elif default is not None:
        prompt = f"  {label} [{hint}] (Enter={default}, '{CLEAR_KEYWORD}'=vacío): "
    else:
        req = " (obligatorio)" if field.get("required") else " (Enter=vacío)"
        prompt = f"  {label} [{hint}]{req}: "

    raw = input(prompt).strip()

    if editing and raw == "":
        return current, False
    if raw == CLEAR_KEYWORD:
        return (None if ftype != "list" else []), True

    if raw == "" and not editing:
        if default is not None:
            return default, True
        if field.get("required"):
            print("    ⚠️  Este campo es obligatorio.")
            return prompt_value(field, current, editing, default)
        return (None if ftype != "list" else []), True

    try:
        value = cast_value(raw, ftype)
    except ValueError:
        print(f"    ⚠️  Valor no válido para tipo {ftype}. Inténtalo de nuevo.")
        return prompt_value(field, current, editing, default)

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


def tmdb_autofill():
    """Pide título/URL/ID, consulta TMDB y devuelve una ficha parcial (o None)."""
    if not tmdb_lookup.get_key():
        print(f"ℹ️  Sin API key de TMDB (busco TMDB_API_KEY o el fichero {tmdb_lookup.KEY_FILE}). Modo manual.")
        return None
    q = input("Título, URL o ID de IMDb (Enter = rellenar a mano): ").strip()
    if not q:
        return None
    try:
        imdb_id = tmdb_lookup.extract_imdb_id(q)
        cands = tmdb_lookup.find_by_imdb(imdb_id) if imdb_id else tmdb_lookup.search_candidates(q)
        if not cands:
            print("Sin resultados en TMDB. Se rellena a mano.")
            return None
        if len(cands) == 1:
            cand = cands[0]
        else:
            for i, c in enumerate(cands, 1):
                print(f"  {i}. {c['label']}")
            ch = input("Número (Enter = rellenar a mano): ").strip()
            if not ch.isdigit() or not (1 <= int(ch) <= len(cands)):
                return None
            cand = cands[int(ch) - 1]
        item = tmdb_lookup.fetch_item(cand)
    except tmdb_lookup.TmdbError as e:
        print(f"⚠️  {e} Se rellena a mano.")
        return None

    print(f"\n  ✔ {item['title']} ({item['type']}) · {item['id']}")
    print(f"    Original: {item['original_title'] or '—'}")
    print(f"    Géneros:  {', '.join(item['genres']) or '—'}")
    if input("¿Es correcto? (S/n): ").strip().lower() == "n":
        return None
    return item


def cmd_add(ds_key):
    data = load_data(ds_key)
    fields = DATASETS[ds_key]["fields"]
    print(f"\nAñadir a «{DATASETS[ds_key]['label']}» (Ctrl+C para cancelar)\n")

    item = {}
    try:
        prefill = tmdb_autofill() or {}
        if prefill.get("id") and any(e.get("id") == prefill["id"] for e in data):
            if input(f"⚠️  Ya existe {prefill['id']!r} en esta lista. ¿Seguir? (s/N): ").strip().lower() != "s":
                print("Cancelado.")
                return
        item = {}
        for field in fields:
            key = field["key"]
            if key in prefill:
                item[key] = prefill[key]
                continue
            if ds_key == "coleccion" and key == "store":
                item["store"], item["gift"] = prompt_store()
                continue
            if ds_key == "coleccion" and key == "gift":
                continue  # ya resuelto al elegir la tienda
            if ds_key == "coleccion" and key == "price" and item.get("gift"):
                item["price"] = None
                continue
            value, _ = prompt_value(field, default=field_defaults(ds_key, item).get(key))
            item[key] = value
        item = {f["key"]: item.get(f["key"]) for f in fields}  # mantiene el orden de campos
    except KeyboardInterrupt:
        print("\nCancelado.")
        return

    new_id = item.get("id")
    if not prefill and new_id and any(e.get("id") == new_id for e in data):
        if input(f"⚠️  Ya existe un elemento con id {new_id!r}. ¿Añadir de todos modos? (s/N): ").strip().lower() != "s":
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
        print("  3) Gestionar backups")
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
            backups_menu()
        else:
            print("Opción no reconocida.")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nHasta luego 👋")
        sys.exit(0)