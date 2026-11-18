"""Accès à l'entrepôt DuckDB pour les notebooks.

Les agrégations lourdes se font en SQL dans DuckDB : seuls les résultats
(quelques milliers de lignes au plus) arrivent dans pandas.
"""
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from config import WAREHOUSE  # noqa: E402


def connect():
    if not WAREHOUSE.exists():
        raise FileNotFoundError(
            f"Entrepôt introuvable ({WAREHOUSE}). Lancer d'abord : python pipeline/run_pipeline.py")
    return duckdb.connect(str(WAREHOUSE), read_only=True)


def query(sql, con=None):
    """Exécute une requête et renvoie un DataFrame."""
    if con is not None:
        return con.execute(sql).df()
    with connect() as c:
        return c.execute(sql).df()


def sample(n=1_000_000, seed=42, where="TRUE", con=None):
    """Échantillon aléatoire reproductible de vols (pour les modèles)."""
    return query(f"""
        SELECT * FROM fact_flights
        WHERE {where}
        USING SAMPLE reservoir({int(n)} ROWS) REPEATABLE ({int(seed)})
    """, con)


def fmt(n):
    """12345678 -> '12 345 678'."""
    return f"{n:,.0f}".replace(",", " ")
