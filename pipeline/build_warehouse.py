"""Étape 4 : entrepôt DuckDB en schéma en étoile.

Tables produites :
  dim_date, dim_carrier, dim_airport          dimensions
  fact_weather_hourly                         météo horaire par aéroport
  fact_flights                                un vol par ligne, croisé avec
                                              la météo de l'aéroport de départ
                                              à l'heure prévue du décollage
"""
import duckdb

from config import SEEDS, STAGING, WAREHOUSE
from utils import log

WEATHER_CONDITION = """
CASE
    WHEN weather_code IS NULL THEN NULL
    WHEN weather_code <= 1 THEN 'Dégagé'
    WHEN weather_code <= 3 THEN 'Nuageux'
    WHEN weather_code IN (45, 48) THEN 'Brouillard'
    WHEN weather_code BETWEEN 51 AND 57 THEN 'Bruine'
    WHEN weather_code BETWEEN 61 AND 67 OR weather_code BETWEEN 80 AND 82 THEN 'Pluie'
    WHEN weather_code BETWEEN 71 AND 77 OR weather_code IN (85, 86) THEN 'Neige'
    WHEN weather_code >= 95 THEN 'Orage'
    ELSE 'Autre'
END
"""


def build(con):
    p = lambda path: path.as_posix()
    flights = p(STAGING / "flights" / "*.parquet")
    weather_files = list((STAGING / "weather").glob("*.parquet"))

    con.execute(f"""
    CREATE OR REPLACE TABLE stg_flights AS
    SELECT * FROM read_parquet('{flights}')
    """)

    con.execute(f"""
    CREATE OR REPLACE TABLE dim_carrier AS
    WITH seen AS (SELECT DISTINCT Reporting_Airline AS carrier_code FROM stg_flights),
         seed AS (SELECT * FROM read_csv_auto('{p(SEEDS / "carriers.csv")}'))
    SELECT s.carrier_code,
           COALESCE(d.carrier_name, s.carrier_code) AS carrier_name,
           COALESCE(d.carrier_type, 'Inconnue') AS carrier_type
    FROM seen s LEFT JOIN seed d USING (carrier_code)
    """)

    if weather_files:
        con.execute(f"""
        CREATE OR REPLACE TABLE fact_weather_hourly AS
        SELECT airport_code,
               CAST(time AS DATE) AS weather_date,
               HOUR(time) AS weather_hour,
               temperature_2m AS temperature_c,
               precipitation AS precipitation_mm,
               snowfall AS snowfall_cm,
               wind_speed_10m AS wind_kmh,
               wind_gusts_10m AS gusts_kmh,
               cloud_cover AS cloud_cover_pct,
               weather_code,
               {WEATHER_CONDITION} AS weather_condition,
               timezone
        FROM read_parquet('{p(STAGING / "weather" / "*.parquet")}')
        -- Au passage à l'heure d'hiver, une heure locale existe deux fois :
        -- on n'en garde qu'une pour ne pas dupliquer les vols à la jointure.
        QUALIFY ROW_NUMBER() OVER (PARTITION BY airport_code, weather_date, weather_hour ORDER BY time) = 1
        """)
    else:
        con.execute("""
        CREATE OR REPLACE TABLE fact_weather_hourly (
            airport_code VARCHAR, weather_date DATE, weather_hour INTEGER,
            temperature_c DOUBLE, precipitation_mm DOUBLE, snowfall_cm DOUBLE,
            wind_kmh DOUBLE, gusts_kmh DOUBLE, cloud_cover_pct DOUBLE,
            weather_code INTEGER, weather_condition VARCHAR, timezone VARCHAR)
        """)

    con.execute(f"""
    CREATE OR REPLACE TABLE dim_airport AS
    WITH used AS (
        SELECT Origin AS airport_code, COUNT(*) AS departures FROM stg_flights GROUP BY 1
        UNION ALL
        SELECT Dest, 0 FROM stg_flights GROUP BY 1
    ),
    agg AS (SELECT airport_code, SUM(departures) AS departures FROM used GROUP BY 1)
    SELECT u.airport_code,
           COALESCE(a.airport_name, u.airport_code) AS airport_name,
           a.city, a.state, a.latitude, a.longitude, a.elevation_ft,
           u.departures,
           u.airport_code IN (SELECT DISTINCT airport_code FROM fact_weather_hourly) AS has_weather
    FROM agg u
    LEFT JOIN read_parquet('{p(STAGING / "airports.parquet")}') a USING (airport_code)
    """)

    con.execute("""
    CREATE OR REPLACE TABLE dim_date AS
    SELECT d::DATE AS date,
           YEAR(d) AS year,
           MONTH(d) AS month,
           ['janv.','févr.','mars','avr.','mai','juin','juil.','août','sept.','oct.','nov.','déc.'][MONTH(d)] AS month_name,
           DAY(d) AS day,
           ISODOW(d) AS weekday,
           ['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche'][ISODOW(d)] AS weekday_name,
           ISODOW(d) >= 6 AS is_weekend,
           WEEKOFYEAR(d) AS week,
           CASE WHEN MONTH(d) IN (12,1,2) THEN 'Hiver' WHEN MONTH(d) IN (3,4,5) THEN 'Printemps'
                WHEN MONTH(d) IN (6,7,8) THEN 'Été' ELSE 'Automne' END AS season
    FROM generate_series(
        (SELECT MIN(FlightDate) FROM stg_flights),
        (SELECT MAX(FlightDate) FROM stg_flights),
        INTERVAL 1 DAY) t(d)
    """)

    con.execute("""
    CREATE OR REPLACE TABLE fact_flights AS
    WITH f AS (
        SELECT
            ROW_NUMBER() OVER (ORDER BY FlightDate, CRSDepTime, Reporting_Airline,
                               Flight_Number_Reporting_Airline, Origin) AS flight_id,
            CAST(FlightDate AS DATE) AS flight_date,
            Reporting_Airline AS carrier_code,
            Flight_Number_Reporting_Airline AS flight_number,
            Tail_Number AS tail_number,
            Origin AS origin,
            Dest AS dest,
            CRSDepTime AS sched_dep_hhmm,
            LEAST(CRSDepTime // 100, 23) AS sched_dep_hour,
            DepDelay AS dep_delay_min,
            ArrDelay AS arr_delay_min,
            COALESCE(ArrDel15, 0) = 1 AS is_delayed,
            Cancelled = 1 AS is_cancelled,
            CASE CancellationCode WHEN 'A' THEN 'Compagnie' WHEN 'B' THEN 'Météo'
                 WHEN 'C' THEN 'Trafic aérien' WHEN 'D' THEN 'Sécurité' END AS cancellation_reason,
            Diverted = 1 AS is_diverted,
            Distance AS distance_miles,
            CarrierDelay AS delay_carrier_min,
            WeatherDelay AS delay_weather_min,
            NASDelay AS delay_nas_min,
            SecurityDelay AS delay_security_min,
            LateAircraftDelay AS delay_late_aircraft_min
        FROM stg_flights
    )
    SELECT f.*,
           CASE WHEN f.sched_dep_hour < 6 THEN 'Nuit (0-6h)'
                WHEN f.sched_dep_hour < 12 THEN 'Matin (6-12h)'
                WHEN f.sched_dep_hour < 18 THEN 'Après-midi (12-18h)'
                ELSE 'Soir (18-24h)' END AS dep_period,
           w.temperature_c, w.precipitation_mm, w.snowfall_cm,
           w.wind_kmh, w.gusts_kmh, w.cloud_cover_pct,
           w.weather_condition
    FROM f
    LEFT JOIN fact_weather_hourly w
      ON w.airport_code = f.origin
     AND w.weather_date = f.flight_date
     AND w.weather_hour = f.sched_dep_hour
    """)
    staged, built = con.execute(
        "SELECT (SELECT COUNT(*) FROM stg_flights), (SELECT COUNT(*) FROM fact_flights)").fetchone()
    if staged != built:
        raise SystemExit(f"La jointure météo a changé le nombre de vols : {staged} -> {built}")
    con.execute("DROP TABLE stg_flights")


QUALITY_CHECKS = [
    # (nom, requête renvoyant une valeur, condition attendue en Python, bloquant)
    ("Vols chargés", "SELECT COUNT(*) FROM fact_flights", lambda v: v > 0, True),
    ("Doublons (date, compagnie, vol, départ, heure)",
     """SELECT COUNT(*) - COUNT(DISTINCT (flight_date, carrier_code, flight_number, origin, sched_dep_hhmm))
        FROM fact_flights""", lambda v: v == 0, False),
    ("Aéroports de départ sans référentiel",
     "SELECT COUNT(*) FROM dim_airport WHERE latitude IS NULL", lambda v: v <= 5, False),
    ("Compagnies sans nom",
     "SELECT COUNT(*) FROM dim_carrier WHERE carrier_type = 'Inconnue'", lambda v: v == 0, False),
    ("Vols annulés avec un retard à l'arrivée",
     "SELECT COUNT(*) FROM fact_flights WHERE is_cancelled AND arr_delay_min IS NOT NULL",
     lambda v: v == 0, False),
    ("Part des retards dont les causes somment au retard (%)",
     """SELECT ROUND(100.0 * AVG(CASE WHEN ABS(delay_carrier_min + delay_weather_min + delay_nas_min
                + delay_security_min + delay_late_aircraft_min - arr_delay_min) <= 1 THEN 1 ELSE 0 END), 1)
        FROM fact_flights WHERE is_delayed AND delay_carrier_min IS NOT NULL""",
     lambda v: v is None or v >= 95, False),
    ("Part des vols croisés avec la météo (%)",
     "SELECT ROUND(100.0 * AVG(CASE WHEN weather_condition IS NOT NULL THEN 1 ELSE 0 END), 1) FROM fact_flights",
     lambda v: v is not None and v >= 50, False),
    ("Jours sans vol dans la période",
     "SELECT COUNT(*) FROM dim_date WHERE date NOT IN (SELECT DISTINCT flight_date FROM fact_flights)",
     lambda v: v == 0, False),
]


def check(con):
    rows = []
    blocking = []
    for name, sql, ok, critical in QUALITY_CHECKS:
        value = con.execute(sql).fetchone()[0]
        passed = bool(ok(value))
        rows.append((name, str(value), passed))
        log.info("%s %-55s %s", "OK " if passed else "!! ", name, value)
        if critical and not passed:
            blocking.append(name)
    con.execute("CREATE OR REPLACE TABLE quality_checks (check_name VARCHAR, value VARCHAR, passed BOOLEAN)")
    con.executemany("INSERT INTO quality_checks VALUES (?, ?, ?)", rows)
    if blocking:
        raise SystemExit(f"Contrôle bloquant en échec : {blocking}")


def run():
    WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(WAREHOUSE)) as con:
        build(con)
        n = con.execute("SELECT COUNT(*) FROM fact_flights").fetchone()[0]
        log.info("Entrepôt construit : %s vols", f"{n:,}".replace(",", " "))
        check(con)


if __name__ == "__main__":
    run()
