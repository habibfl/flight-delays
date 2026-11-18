"""Exécute les requêtes de sql/ sur l'entrepôt et écrit sql/RESULTATS.md."""
import os
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "pipeline"))
from config import WAREHOUSE  # noqa: E402


def run(out=HERE / "RESULTATS.md"):
    parts = ["# Résultats des requêtes SQL\n",
             "Généré par `python sql/run_all.py` sur l'entrepôt DuckDB.\n"]
    with duckdb.connect(str(WAREHOUSE), read_only=True) as con:
        for f in sorted(HERE.glob("[0-9]*.sql")):
            sql = f.read_text(encoding="utf-8")
            title = " ".join(l.lstrip("- ").strip() for l in sql.splitlines()
                             if l.startswith("--"))
            df = con.execute(sql).df()
            parts.append(f"\n## {f.stem}\n\n{title}\n\n{df.to_markdown(index=False)}\n")
            print(f"{f.name}: {len(df)} lignes")
    out.write_text("".join(parts), encoding="utf-8")
    return out


if __name__ == "__main__":
    print("Écrit", run())
