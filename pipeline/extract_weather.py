"""Étape 3 : météo horaire des aéroports les plus fréquentés (API Open-Meteo).

Un appel par aéroport couvre toute la période. Les heures sont renvoyées
en heure locale de l'aéroport (timezone=auto), comme les horaires des vols
BTS : la jointure se fait donc directement sur la date et l'heure locales.
"""
import time

import duckdb
import pandas as pd

from config import STAGING, TOP_AIRPORTS, WEATHER_URL, WEATHER_VARS
from utils import get, log


def top_airports():
    con = duckdb.connect()
    flights = (STAGING / "flights" / "*.parquet").as_posix()
    airports = (STAGING / "airports.parquet").as_posix()
    return con.execute(
        f"""
        SELECT f.Origin AS code, a.latitude, a.longitude, COUNT(*) AS n,
               MIN(f.FlightDate)::DATE AS d0, MAX(f.FlightDate)::DATE AS d1
        FROM read_parquet('{flights}') f
        JOIN read_parquet('{airports}') a ON a.airport_code = f.Origin
        GROUP BY ALL
        ORDER BY n DESC
        LIMIT {TOP_AIRPORTS}
        """
    ).df()


def fetch(code, lat, lon, d0, d1):
    r = get(
        WEATHER_URL,
        params={
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "start_date": pd.Timestamp(d0).strftime("%Y-%m-%d"),
            "end_date": pd.Timestamp(d1).strftime("%Y-%m-%d"),
            "hourly": ",".join(WEATHER_VARS),
            "timezone": "auto",
        },
    )
    js = r.json()
    df = pd.DataFrame(js["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df.insert(0, "airport_code", code)
    df["timezone"] = js.get("timezone")
    return df


def run():
    out_dir = STAGING / "weather"
    out_dir.mkdir(parents=True, exist_ok=True)
    top = top_airports()
    share = top["n"].sum()
    log.info("Météo pour %d aéroports", len(top))
    for i, row in enumerate(top.itertuples(), 1):
        out = out_dir / f"{row.code}.parquet"
        if out.exists():
            continue
        df = fetch(row.code, row.latitude, row.longitude, row.d0, row.d1)
        df.to_parquet(out, index=False)
        log.info("[%d/%d] %s : %d heures", i, len(top), row.code, len(df))
        time.sleep(1)  # API gratuite : on reste poli
    log.info("Météo prête (%s vols au départ de ces aéroports)",
             f"{share:,}".replace(",", " "))


if __name__ == "__main__":
    run()
