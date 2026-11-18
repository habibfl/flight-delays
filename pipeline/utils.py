"""Outils partagés : journalisation et téléchargement avec reprise."""
import logging
import time
from pathlib import Path

import requests

from config import USER_AGENT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pipeline")


def get(url, params=None, retries=4, timeout=120, stream=False):
    """GET avec nouvelles tentatives espacées (1 s, 2 s, 4 s...)."""
    for attempt in range(retries):
        try:
            r = requests.get(
                url,
                params=params,
                timeout=timeout,
                stream=stream,
                headers={"User-Agent": USER_AGENT},
            )
            if r.status_code == 429:
                raise requests.HTTPError("429 trop de requêtes")
            if 400 <= r.status_code < 500:
                # Erreur de requête : inutile de réessayer, on affiche la raison donnée par le serveur.
                raise ValueError(f"{r.status_code} pour {r.url} : {r.text[:300]}")
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            log.warning("Échec (%s), nouvelle tentative dans %d s", e, wait)
            time.sleep(wait)


def download(url, dest: Path, min_bytes=1000):
    """Télécharge un fichier une seule fois. Écrit dans un .part puis renomme,
    pour ne jamais laisser un fichier incomplet passer pour un fichier valide."""
    if dest.exists() and dest.stat().st_size >= min_bytes:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with get(url, stream=True, timeout=300) as r, open(tmp, "wb") as f:
        for chunk in r.iter_content(1 << 20):
            f.write(chunk)
    if tmp.stat().st_size < min_bytes:
        tmp.unlink()
        raise RuntimeError(f"Fichier trop petit : {url}")
    tmp.replace(dest)
    return True
