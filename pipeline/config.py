"""Paramètres communs du pipeline."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# FD_DATA permet aux tests de travailler dans un dossier temporaire.
DATA = Path(os.environ.get("FD_DATA", ROOT / "data"))
RAW = DATA / "raw"
STAGING = DATA / "staging"
SEEDS = ROOT / "data" / "seeds"
WAREHOUSE = DATA / "warehouse" / "flights.duckdb"
EXPORT = DATA / "powerbi"

YEARS = [2024, 2025]
MONTHS = range(1, 13)

# Nombre d'aéroports de départ pour lesquels on récupère la météo
# (les plus fréquentés, environ 80 % des vols pour 50 aéroports).
TOP_AIRPORTS = 50

BTS_URL = (
    "https://transtats.bts.gov/PREZIP/"
    "On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
)
AIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_VARS = [
    "temperature_2m",
    "precipitation",
    "snowfall",
    "wind_speed_10m",
    "wind_gusts_10m",
    "cloud_cover",
    "weather_code",
]

# Colonnes conservées dans les fichiers BTS (une centaine au total).
FLIGHT_COLUMNS = {
    "FlightDate": "string",
    "Reporting_Airline": "string",
    "Flight_Number_Reporting_Airline": "string",
    "Tail_Number": "string",
    "Origin": "string",
    "Dest": "string",
    "CRSDepTime": "Int64",
    "DepTime": "Int64",
    "DepDelay": "Float64",
    "DepDel15": "Float64",
    "CRSArrTime": "Int64",
    "ArrDelay": "Float64",
    "ArrDel15": "Float64",
    "Cancelled": "Float64",
    "CancellationCode": "string",
    "Diverted": "Float64",
    "Distance": "Float64",
    "CarrierDelay": "Float64",
    "WeatherDelay": "Float64",
    "NASDelay": "Float64",
    "SecurityDelay": "Float64",
    "LateAircraftDelay": "Float64",
}

USER_AGENT = "flight-delays-portfolio/1.0 (github.com/habibfl)"
