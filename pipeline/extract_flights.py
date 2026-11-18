"""Étape 1 : vols commerciaux américains (BTS, un fichier ZIP par mois).

Chaque ZIP contient un CSV d'une centaine de colonnes (~250 Mo décompressé).
On ne garde que les colonnes utiles et on écrit un Parquet par mois,
beaucoup plus léger et rapide à relire.
"""
import zipfile

import pandas as pd
import requests

from config import BTS_URL, FLIGHT_COLUMNS, MONTHS, RAW, STAGING, YEARS
from utils import download, log


def convert(zip_path, out_path):
    with zipfile.ZipFile(zip_path) as z:
        csv_name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(csv_name) as f:
            df = pd.read_csv(
                f,
                usecols=list(FLIGHT_COLUMNS),
                dtype=FLIGHT_COLUMNS,
                low_memory=False,
            )
    df["FlightDate"] = pd.to_datetime(df["FlightDate"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    return len(df)


def run():
    total = 0
    for year in YEARS:
        for month in MONTHS:
            zip_path = RAW / "flights" / f"{year}_{month:02d}.zip"
            out_path = STAGING / "flights" / f"{year}_{month:02d}.parquet"
            if out_path.exists():
                continue
            try:
                if download(BTS_URL.format(year=year, month=month), zip_path):
                    log.info("Téléchargé %s", zip_path.name)
            except (requests.HTTPError, ValueError) as e:
                log.warning("%d-%02d indisponible (%s), ignoré", year, month, e)
                continue
            n = convert(zip_path, out_path)
            total += n
            log.info("%d-%02d : %s vols", year, month, f"{n:,}".replace(",", " "))
    files = sorted((STAGING / "flights").glob("*.parquet"))
    log.info("Vols : %d fichiers mensuels prêts (%s nouveaux vols)", len(files), total)


if __name__ == "__main__":
    run()
