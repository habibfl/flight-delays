"""Étape 5 : export des tables pour Power BI (Parquet, lu nativement).

En plus des tables du schéma en étoile, une table agrégée par jour,
aéroport et compagnie permet des visuels rapides sans charger chaque vol.
"""
import duckdb

from config import EXPORT, WAREHOUSE
from utils import log

TABLES = ["dim_date", "dim_carrier", "dim_airport", "fact_flights", "quality_checks"]

AGG_DAILY = """
SELECT flight_date, origin, carrier_code,
       COUNT(*) AS flights,
       SUM(is_delayed::INT) AS delayed,
       SUM(is_cancelled::INT) AS cancelled,
       SUM(GREATEST(arr_delay_min, 0)) AS delay_minutes,
       SUM(delay_carrier_min) AS carrier_min,
       SUM(delay_weather_min) AS weather_min,
       SUM(delay_nas_min) AS nas_min,
       SUM(delay_security_min) AS security_min,
       SUM(delay_late_aircraft_min) AS late_aircraft_min
FROM fact_flights
GROUP BY ALL
"""


def run():
    EXPORT.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(WAREHOUSE), read_only=True) as con:
        for t in TABLES:
            out = (EXPORT / f"{t}.parquet").as_posix()
            con.execute(f"COPY {t} TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            log.info("Exporté %s", out.rsplit("/", 1)[-1])
        out = (EXPORT / "agg_daily.parquet").as_posix()
        con.execute(f"COPY ({AGG_DAILY}) TO '{out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        log.info("Exporté agg_daily.parquet")
    log.info("Fichiers Power BI dans %s", EXPORT)


if __name__ == "__main__":
    run()
