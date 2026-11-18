"""Jeu de données simulé au format exact des sources, pour tester le pipeline
de bout en bout sans réseau."""
import io
import os
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

AIRPORTS = {
    "ATL": (33.6367, -84.4281, "US-GA"),
    "ORD": (41.9786, -87.9048, "US-IL"),
    "DFW": (32.8968, -97.0380, "US-TX"),
    "DEN": (39.8617, -104.6731, "US-CO"),
    "JFK": (40.6398, -73.7789, "US-NY"),
}
CARRIERS = ["AA", "DL", "UA", "WN"]


def fake_month(year, month, rng, n=400):
    days = pd.date_range(f"{year}-{month:02d}-01", periods=pd.Period(f"{year}-{month}").days_in_month)
    codes = list(AIRPORTS)
    origin = rng.choice(codes, n)
    dest = np.array([rng.choice([c for c in codes if c != o]) for o in origin])
    dep = rng.integers(5, 23, n) * 100 + rng.choice([0, 15, 30, 45], n)
    delay = np.round(rng.gamma(1.2, 18, n) - 12)
    cancelled = (rng.random(n) < 0.02).astype(float)
    arr = np.where(cancelled == 1, np.nan, delay + rng.integers(-5, 6, n))
    del15 = np.where(cancelled == 1, np.nan, (arr >= 15).astype(float))
    causes = np.where((del15 == 1)[:, None], 0.0, np.nan).repeat(5, axis=1)
    for i in np.where(del15 == 1)[0]:
        share = rng.dirichlet(np.ones(5))
        parts = np.floor(share * arr[i])
        parts[0] += arr[i] - parts.sum()
        causes[i] = parts
    df = pd.DataFrame({
        "Year": year, "Quarter": (month - 1) // 3 + 1, "Month": month,
        "FlightDate": rng.choice(days, n).astype("datetime64[D]").astype(str),
        "Reporting_Airline": rng.choice(CARRIERS, n),
        "Tail_Number": [f"N{x}" for x in rng.integers(100, 999, n)],
        "Flight_Number_Reporting_Airline": rng.integers(1, 9000, n),
        "Origin": origin, "Dest": dest,
        "CRSDepTime": dep, "DepTime": dep + delay.astype(int),
        "DepDelay": np.where(cancelled == 1, np.nan, delay),
        "DepDel15": np.where(cancelled == 1, np.nan, (delay >= 15).astype(float)),
        "CRSArrTime": (dep + 200) % 2400,
        "ArrDelay": arr, "ArrDel15": del15,
        "Cancelled": cancelled,
        "CancellationCode": np.where(cancelled == 1, rng.choice(list("ABC"), n), ""),
        "Diverted": 0.0, "Distance": rng.integers(300, 2500, n).astype(float),
        "CarrierDelay": causes[:, 0], "WeatherDelay": causes[:, 1], "NASDelay": causes[:, 2],
        "SecurityDelay": causes[:, 3], "LateAircraftDelay": causes[:, 4],
        "DivAirportLandings": 0,
    })
    return df


def fake_weather(params):
    # Open-Meteo refuse toute date qui n'est pas au format AAAA-MM-JJ.
    import re
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", params["start_date"]), params["start_date"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", params["end_date"]), params["end_date"]
    days = pd.date_range(params["start_date"], params["end_date"] + " 23:00", freq="h")
    rng = np.random.default_rng(int(abs(params["latitude"]) * 100))
    n = len(days)
    return {
        "timezone": "America/New_York",
        "hourly": {
            "time": days.strftime("%Y-%m-%dT%H:%M").tolist(),
            "temperature_2m": rng.normal(12, 8, n).round(1).tolist(),
            "precipitation": rng.exponential(0.3, n).round(1).tolist(),
            "snowfall": np.zeros(n).tolist(),
            "wind_speed_10m": rng.gamma(2, 8, n).round(1).tolist(),
            "wind_gusts_10m": rng.gamma(2, 14, n).round(1).tolist(),
            "cloud_cover": rng.integers(0, 101, n).tolist(),
            "weather_code": rng.choice([0, 1, 3, 45, 61, 71, 95], n).tolist(),
        },
    }


@pytest.fixture(scope="session")
def pipeline_data(tmp_path_factory):
    data = tmp_path_factory.mktemp("data")
    os.environ["FD_DATA"] = str(data)
    rng = np.random.default_rng(0)

    flights_dir = data / "raw" / "flights"
    flights_dir.mkdir(parents=True)
    for m in (1, 2):
        buf = io.StringIO()
        fake_month(2024, m, rng).to_csv(buf, index=False)
        with zipfile.ZipFile(flights_dir / f"2024_{m:02d}.zip", "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(f"On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2024_{m}.csv", buf.getvalue())
            z.writestr("readme.html", "<html></html>")

    rows = [{"id": i, "ident": "K" + c, "type": "large_airport", "name": f"{c} International",
             "latitude_deg": lat, "longitude_deg": lon, "elevation_ft": 100, "continent": "NA",
             "iso_country": "US", "iso_region": reg, "municipality": c.title(),
             "scheduled_service": "yes", "gps_code": "K" + c, "iata_code": c}
            for i, (c, (lat, lon, reg)) in enumerate(AIRPORTS.items())]
    rows.append({**rows[0], "id": 99, "type": "closed", "name": "Old ATL"})
    pd.DataFrame(rows).to_csv(data / "raw" / "airports.csv", index=False)

    # FD_DATA est lu à l'import de config : on importe après l'avoir fixé.
    import extract_flights, extract_airports, extract_weather, build_warehouse, export_powerbi
    from types import SimpleNamespace
    extract_flights.YEARS, extract_flights.MONTHS = [2024], [1, 2]

    class Resp:
        def __init__(self, js): self._js = js
        def json(self): return self._js
    extract_weather.get = lambda url, params=None, **k: Resp(fake_weather(params))
    extract_weather.time = SimpleNamespace(sleep=lambda s: None)

    extract_flights.run()
    extract_airports.run()
    extract_weather.run()
    build_warehouse.run()
    export_powerbi.run()
    return data
