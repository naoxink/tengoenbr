#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalize_stores.py  (script de un solo uso)
============================================
Normaliza el campo `store` de data.json:
  - Unifica mayúsculas/minúsculas y alias:  Cex/cex -> CEX,  El Corte Inglés -> ECI ...
  - store == "Regalo"  ->  store = null  y  gift = true

Por defecto es un ENSAYO: sólo muestra qué cambiaría y no toca nada.
Para aplicar los cambios:   python normalize_stores.py --apply
(antes se crea un backup en backups/coleccion/, como hace manage_lists.py)
"""

import json
import os
import shutil
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
BACKUP_DIR = os.path.join(BASE_DIR, "backups", "coleccion")

# nombre en minúsculas -> nombre canónico
CANONICAL = {
    "eci": "ECI",
    "el corte inglés": "ECI",
    "el corte ingles": "ECI",
    "cex": "CEX",
    "fnac": "Fnac",
    "amazon": "Amazon",
    "game": "Game",
    "mediamarkt": "MediaMarkt",
    "media markt": "MediaMarkt",
}
GIFT_WORDS = {"regalo"}


def main():
    apply = "--apply" in sys.argv

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    changes = []
    unknown = {}
    for item in data:
        store = item.get("store")
        if store is None:
            continue
        key = str(store).strip().lower()

        if key in GIFT_WORDS:
            changes.append((item.get("title"), f"store={store!r} -> null, gift -> true"))
            item["store"] = None
            item["gift"] = True
        elif key in CANONICAL:
            new = CANONICAL[key]
            if new != store:
                changes.append((item.get("title"), f"store {store!r} -> {new!r}"))
                item["store"] = new
        else:
            unknown[store] = unknown.get(store, 0) + 1

    if changes:
        print(f"{len(changes)} cambio(s):")
        for title, what in changes:
            print(f"  · {title}: {what}")
    else:
        print("Nada que normalizar.")

    if unknown:
        print("\nTiendas no reconocidas (se dejan como están):")
        for name, n in sorted(unknown.items()):
            print(f"  · {name!r} ({n})")
        print("  Si alguna es una variante de otra, añádela al diccionario CANONICAL.")

    if not changes:
        return
    if not apply:
        print("\nEnsayo: no se ha modificado nada. Ejecuta con --apply para aplicar.")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"data_{stamp}.json")
    shutil.copy2(DATA_FILE, dest)
    print(f"\n🗂️  Backup creado: {os.path.relpath(dest, BASE_DIR)}")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")
    print(f"✅ Guardado en data.json ({len(data)} elementos).")


if __name__ == "__main__":
    main()