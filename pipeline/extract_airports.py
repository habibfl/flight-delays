"""Étape 2 : référentiel des aéroports (OurAirports, CSV mondial).

On garde les aéroports qui ont un code IATA, avec leurs coordonnées :
elles servent à interroger l'API météo.
"""
import pandas as pd

from config import AIRPORTS_URL, RAW, STAGING
from utils import download, log


def run():
    raw = RAW / "airports.csv"
    if download(AIRPORTS_URL, raw, min_bytes=100):
        log.info("Téléchargé airports.csv")
    df = pd.read_csv(raw, keep_default_na=False, na_values=[""])
    df = df[df["iata_code"].notna() & (df["iata_code"].str.len() == 3)]
    df = df.rename(
        columns={
            "iata_code": "airport_code",
            "name": "airport_name",
            "municipality": "city",
            "iso_region": "region",
            "iso_country": "country",
            "latitude_deg": "latitude",
            "longitude_deg": "longitude",
            "elevation_ft": "elevation_ft",
            "type": "airport_type",
        }
    )
    cols = ["airport_code", "airport_name", "city", "region", "country",
            "latitude", "longitude", "elevation_ft", "airport_type"]
    # Un même code IATA peut apparaître deux fois (ancien terrain fermé) :
    # on garde le plus grand aéroport.
    rank = {"large_airport": 0, "medium_airport": 1, "small_airport": 2}
    df["_r"] = df["airport_type"].map(rank).fillna(9)
    df = df.sort_values("_r").drop_duplicates("airport_code")[cols]
    df["state"] = df["region"].str.split("-").str[-1]
    out = STAGING / "airports.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    log.info("Aéroports : %d avec code IATA", len(df))


if __name__ == "__main__":
    run()
