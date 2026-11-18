"""Exporte les chiffres et séries agrégées du site dans site/public/data/story.json.

À lancer après le pipeline (et après le notebook du modèle pour la partie modèle) :
    python analysis/export_site.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fd_data as fd  # noqa: E402
from config import EXPORT  # noqa: E402

OUT = HERE.parent / "site" / "public" / "data" / "story.json"


def wilson(k, n, z=1.96):
    p = k / n
    centre = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return centre - half, centre + half


def records(df, digits=4):
    out = []
    for row in df.to_dict(orient="records"):
        clean = {}
        for k, v in row.items():
            if isinstance(v, (np.integer,)):
                v = int(v)
            elif isinstance(v, (float, np.floating)):
                v = None if math.isnan(v) else round(float(v), digits)
            elif isinstance(v, pd.Timestamp):
                v = v.strftime("%Y-%m-%d")
            elif isinstance(v, (np.bool_,)):
                v = bool(v)
            clean[k] = v
        out.append(clean)
    return out


def kpis(con):
    k = fd.query("""
        SELECT COUNT(*) AS flights,
               AVG(is_delayed::INT) AS delayed,
               AVG(is_cancelled::INT) AS cancelled,
               AVG(arr_delay_min) FILTER (WHERE is_delayed) AS avg_delay,
               SUM(GREATEST(arr_delay_min, 0)) / 60 AS hours_lost,
               COUNT(DISTINCT carrier_code) AS carriers,
               COUNT(DISTINCT origin) AS airports,
               MIN(flight_date) AS start, MAX(flight_date) AS end,
               AVG(CASE WHEN weather_condition IS NOT NULL THEN 1 ELSE 0 END) AS weather_share
        FROM fact_flights""", con)
    k["weather_airports"] = fd.query(
        "SELECT COUNT(*) FROM dim_airport WHERE has_weather", con).iloc[0, 0]
    k["flights_per_day"] = k["flights"] / fd.query("SELECT COUNT(*) FROM dim_date", con).iloc[0, 0]
    return records(k)[0]


def monthly(con):
    return records(fd.query("""
        SELECT d.year, d.month, COUNT(*) AS flights, AVG(f.is_delayed::INT) AS delayed,
               AVG(f.is_cancelled::INT) AS cancelled
        FROM fact_flights f JOIN dim_date d ON d.date = f.flight_date
        GROUP BY 1, 2 ORDER BY 1, 2""", con))


def hourly(con):
    return records(fd.query("""
        SELECT sched_dep_hour AS hour, COUNT(*) AS flights, AVG(is_delayed::INT) AS delayed,
               AVG(dep_delay_min) AS avg_dep_delay
        FROM fact_flights WHERE NOT is_cancelled
        GROUP BY 1 HAVING COUNT(*) >= 1000 ORDER BY 1""", con))


def causes(con):
    c = fd.query("""
        SELECT SUM(delay_carrier_min) AS carrier, SUM(delay_late_aircraft_min) AS late_aircraft,
               SUM(delay_nas_min) AS nas, SUM(delay_weather_min) AS weather,
               SUM(delay_security_min) AS security
        FROM fact_flights WHERE is_delayed""", con).iloc[0]
    total = c.sum()
    labels = {"carrier": "Compagnie", "late_aircraft": "Avion arrivé en retard",
              "nas": "Trafic aérien", "weather": "Météo extrême", "security": "Sécurité"}
    return [{"key": k, "label": labels[k], "minutes": float(v), "share": round(float(v / total), 4)}
            for k, v in c.sort_values(ascending=False).items()]


def weather(con):
    w = fd.query("""
        SELECT weather_condition AS condition, COUNT(*) AS flights,
               SUM(is_delayed::INT) AS delayed_n, AVG(is_cancelled::INT) AS cancelled
        FROM fact_flights WHERE weather_condition IS NOT NULL GROUP BY 1""", con)
    w["delayed"] = w.delayed_n / w.flights
    w["lo"], w["hi"] = wilson(w.delayed_n, w.flights)
    return records(w.drop(columns="delayed_n").sort_values("delayed"))


def weather_adjusted(con, n=500_000):
    """Odds ratio de retard par condition météo, à heure, mois, jour, aéroport
    et compagnie égaux (régression logistique sur un échantillon)."""
    import statsmodels.formula.api as smf
    s = fd.sample(n, where="weather_condition IS NOT NULL AND NOT is_cancelled", con=con)
    s["mois"] = pd.to_datetime(s.flight_date).dt.month
    s["jour"] = pd.to_datetime(s.flight_date).dt.day_of_week
    s["retard"] = s.is_delayed.astype(int)
    import statsmodels.api as sm
    # GLM binomial (moindres carrés repondérés) : même modèle logistique, convergence plus robuste.
    m = smf.glm("retard ~ C(weather_condition, Treatment('Dégagé')) + C(sched_dep_hour)"
                " + C(mois) + C(jour) + C(origin) + C(carrier_code)", data=s,
                family=sm.families.Binomial()).fit()
    rows = [ix for ix in m.params.index if ix.startswith("C(weather_condition")]
    ci = m.conf_int()
    return records(pd.DataFrame({
        "condition": [ix.split("[T.")[1].rstrip("]") for ix in rows],
        "odds_ratio": np.exp(m.params[rows]).values,
        "lo": np.exp(ci.loc[rows, 0]).values,
        "hi": np.exp(ci.loc[rows, 1]).values,
    }).sort_values("odds_ratio"))


def gusts(con):
    return records(fd.query("""
        SELECT LEAST(FLOOR(gusts_kmh / 10) * 10, 80)::INT AS gusts, COUNT(*) AS flights,
               AVG(is_delayed::INT) AS delayed, AVG(is_cancelled::INT) AS cancelled
        FROM fact_flights WHERE gusts_kmh IS NOT NULL
        GROUP BY 1 HAVING COUNT(*) >= 500 ORDER BY 1""", con))


def cascade(con):
    c = fd.query("""
        WITH legs AS (
            SELECT is_delayed, LAG(is_delayed) OVER w AS prev_delayed, ROW_NUMBER() OVER w AS rang
            FROM fact_flights
            WHERE tail_number IS NOT NULL AND NOT is_cancelled
            WINDOW w AS (PARTITION BY tail_number, flight_date ORDER BY sched_dep_hhmm)
        )
        SELECT LEAST(rang, 6) AS rank, prev_delayed, COUNT(*) AS flights, SUM(is_delayed::INT) AS delayed_n
        FROM legs GROUP BY 1, 2""", con)
    by_rank = c.groupby("rank")[["flights", "delayed_n"]].sum().reset_index()
    by_rank["delayed"] = by_rank.delayed_n / by_rank.flights
    prev = c.dropna(subset=["prev_delayed"]).groupby("prev_delayed")[["flights", "delayed_n"]].sum()
    after = {str(bool(k)).lower(): round(float(v.delayed_n / v.flights), 4) for k, v in prev.iterrows()}
    return {"by_rank": records(by_rank.drop(columns="delayed_n")), "after_previous": after}


def carriers(con):
    c = fd.query("""
        SELECT c.carrier_code AS code, c.carrier_name AS name, c.carrier_type AS type, d.year,
               COUNT(*) AS flights, SUM(f.is_delayed::INT) AS delayed_n, AVG(f.is_cancelled::INT) AS cancelled
        FROM fact_flights f JOIN dim_carrier c USING (carrier_code) JOIN dim_date d ON d.date = f.flight_date
        GROUP BY ALL""", con)
    tot = c.groupby(["code", "name", "type"], as_index=False).agg(
        flights=("flights", "sum"), delayed_n=("delayed_n", "sum"))
    tot = tot[tot.flights >= 20_000].copy()
    tot["delayed"] = tot.delayed_n / tot.flights
    tot["lo"], tot["hi"] = wilson(tot.delayed_n, tot.flights)
    per_year = c.assign(delayed=c.delayed_n / c.flights).pivot_table(index="code", columns="year", values="delayed")
    for y in per_year.columns:
        tot[f"delayed_{y}"] = tot.code.map(per_year[y])
    canc = c.groupby("code").apply(lambda g: np.average(g.cancelled, weights=g.flights), include_groups=False)
    tot["cancelled"] = tot.code.map(canc)
    return records(tot.drop(columns="delayed_n").sort_values("delayed"))


def airports(con):
    return records(fd.query("""
        SELECT a.airport_code AS code, a.airport_name AS name, a.city, a.state,
               a.latitude AS lat, a.longitude AS lon,
               COUNT(*) AS flights, AVG(f.is_delayed::INT) AS delayed, AVG(f.is_cancelled::INT) AS cancelled
        FROM fact_flights f JOIN dim_airport a ON a.airport_code = f.origin
        WHERE a.latitude IS NOT NULL
        GROUP BY ALL HAVING COUNT(*) >= 20000
        ORDER BY flights DESC""", con))


def model():
    f = EXPORT / "model_scores.parquet"
    if not f.exists():
        return None
    out = {"scores": records(pd.read_parquet(f))}
    for name in ("calibration", "importance"):
        g = EXPORT / f"model_{name}.parquet"
        if g.exists():
            out[name] = records(pd.read_parquet(g))
    return out


def run():
    with fd.connect() as con:
        story = {
            "kpis": kpis(con),
            "monthly": monthly(con),
            "hourly": hourly(con),
            "causes": causes(con),
            "weather": weather(con),
            "weather_adjusted": weather_adjusted(con),
            "gusts": gusts(con),
            "cascade": cascade(con),
            "carriers": carriers(con),
            "airports": airports(con),
            "quality": records(fd.query("SELECT * FROM quality_checks", con)),
            "model": model(),
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(story, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Écrit {OUT} ({OUT.stat().st_size / 1024:.0f} Ko)")


if __name__ == "__main__":
    run()
