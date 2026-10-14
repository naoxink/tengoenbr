# -*- coding: utf-8 -*-
"""
tmdb_lookup.py
==============
Autorrelleno de fichas para manage_lists.py usando la API de TMDB.

Sólo usa la librería estándar (urllib), no hay que instalar nada.

API key (gratuita, themoviedb.org -> Ajustes -> API): se lee de
  1) la variable de entorno TMDB_API_KEY, o
  2) un fichero `.tmdb_key` junto a este script (¡añádelo al .gitignore!).
Vale tanto la "API Key" (v3, 32 caracteres) como el "Read Access Token" (v4, empieza por eyJ).
"""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, ".tmdb_key")
API = "https://api.themoviedb.org/3"
LANG = "es-ES"

# TMDB -> vocabulario que ya usas en tus JSON. Edítalo a tu gusto.
# Un valor puede ser un str o una lista (un género de TMDB -> varios tuyos).
GENRE_MAP = {
    "Familia": "Familiar",
    "Bélica": "Bélico",
    "Western": "Del oeste",
    "Película de TV": None,          # None = descartar
    "Action & Adventure": ["Acción", "Aventura"],
    "Sci-Fi & Fantasy": ["Ciencia ficción", "Fantasía"],
    "War & Politics": ["Bélico"],
    "Kids": "Familiar",
    "Soap": "Drama",
    "Talk": None,
    "News": None,
}


class TmdbError(Exception):
    pass


def get_key():
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if not key and os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            key = f.read().strip()
    return key or None


def _get(path, **params):
    key = get_key()
    if not key:
        raise TmdbError("No hay API key de TMDB (variable TMDB_API_KEY o fichero .tmdb_key).")
    headers = {"accept": "application/json", "User-Agent": "tengoenbr-manage-lists"}
    params = {k: v for k, v in params.items() if v is not None}
    if key.startswith("eyJ"):                     # token v4
        headers["Authorization"] = f"Bearer {key}"
    else:                                         # clave v3
        params["api_key"] = key
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise TmdbError("TMDB rechazó la API key (401). Revísala.")
        raise TmdbError(f"Error HTTP {e.code} al consultar TMDB.")
    except (urllib.error.URLError, TimeoutError) as e:
        raise TmdbError(f"No se pudo conectar con TMDB: {e}")


# ---------------------------------------------------------------------------
# Entrada: ¿es un ID/URL de IMDb o un título?
# ---------------------------------------------------------------------------

_IMDB_RE = re.compile(r"(tt\d{6,10})")


def extract_imdb_id(text):
    m = _IMDB_RE.search(text or "")
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Búsqueda
# ---------------------------------------------------------------------------

def _year(date_str):
    return (date_str or "")[:4] or "?"


def search_candidates(query, limit=8):
    """Devuelve una lista de candidatos [{media_type, tmdb_id, label}, ...]."""
    data = _get("/search/multi", query=query, language=LANG, include_adult="false")
    out = []
    for r in data.get("results", []):
        mt = r.get("media_type")
        if mt not in ("movie", "tv"):
            continue
        if mt == "movie":
            title, orig, date = r.get("title"), r.get("original_title"), r.get("release_date")
            kind = "Película"
        else:
            title, orig, date = r.get("name"), r.get("original_name"), r.get("first_air_date")
            kind = "Serie"
        label = f"{title} ({_year(date)}) · {kind}"
        if orig and orig != title:
            label += f" · orig: {orig}"
        out.append({"media_type": mt, "tmdb_id": r["id"], "label": label})
        if len(out) >= limit:
            break
    return out


def find_by_imdb(imdb_id):
    """Devuelve [candidato] (0 ó 1 elemento) a partir de un tt… de IMDb."""
    data = _get(f"/find/{imdb_id}", external_source="imdb_id", language=LANG)
    for mt, key in (("movie", "movie_results"), ("tv", "tv_results")):
        for r in data.get(key, []):
            title = r.get("title") or r.get("name")
            return [{"media_type": mt, "tmdb_id": r["id"], "label": title}]
    return []


# ---------------------------------------------------------------------------
# Detalle -> ficha con el formato de tus JSON
# ---------------------------------------------------------------------------

def _map_genres(names):
    result = []
    for n in names:
        mapped = GENRE_MAP.get(n, n)
        if mapped is None:
            continue
        for g in ([mapped] if isinstance(mapped, str) else mapped):
            if g not in result:
                result.append(g)
    return result


def fetch_item(candidate):
    """Devuelve un dict con id, title, original_title, url, type, genres."""
    mt, tid = candidate["media_type"], candidate["tmdb_id"]
    d = _get(f"/{mt}/{tid}", language=LANG, append_to_response="external_ids")

    if mt == "movie":
        imdb_id = d.get("imdb_id") or (d.get("external_ids") or {}).get("imdb_id")
        title, orig = d.get("title"), d.get("original_title")
        kind = "Película"
    else:
        imdb_id = (d.get("external_ids") or {}).get("imdb_id")
        title, orig = d.get("name"), d.get("original_name")
        kind = "MiniSerie" if d.get("type") == "Miniseries" else "Serie"

    if not imdb_id:
        raise TmdbError("TMDB no tiene el ID de IMDb de este título; añádelo a mano.")

    return {
        "id": imdb_id,
        "title": title,
        "original_title": orig if orig and orig != title else None,
        "url": f"https://www.imdb.com/title/{imdb_id}/",
        "type": kind,
        "genres": _map_genres([g["name"] for g in d.get("genres", [])]),
    }