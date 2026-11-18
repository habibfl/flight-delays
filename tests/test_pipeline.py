"""Le pipeline complet tourne sur données simulées et produit un entrepôt cohérent."""
import duckdb
import pandas as pd


def q(data, sql):
    with duckdb.connect(str(data / "warehouse" / "flights.duckdb"), read_only=True) as con:
        return con.execute(sql).fetchone()[0]


def test_staging_keeps_only_useful_columns(pipeline_data):
    df = pd.read_parquet(pipeline_data / "staging" / "flights" / "2024_01.parquet")
    assert "DivAirportLandings" not in df.columns
    assert len(df) == 400


def test_all_flights_loaded(pipeline_data):
    assert q(pipeline_data, "SELECT COUNT(*) FROM fact_flights") == 800


def test_flight_ids_unique(pipeline_data):
    assert q(pipeline_data, "SELECT COUNT(*) - COUNT(DISTINCT flight_id) FROM fact_flights") == 0


def test_closed_duplicate_airport_dropped(pipeline_data):
    assert q(pipeline_data, "SELECT airport_name FROM dim_airport WHERE airport_code='ATL'") == "ATL International"


def test_every_flight_crossed_with_weather(pipeline_data):
    assert q(pipeline_data, "SELECT COUNT(*) FROM fact_flights WHERE weather_condition IS NULL") == 0


def test_weather_join_matches_hour(pipeline_data):
    mismatches = q(pipeline_data, """
        SELECT COUNT(*) FROM fact_flights f JOIN fact_weather_hourly w
          ON w.airport_code = f.origin AND w.weather_date = f.flight_date
         AND w.weather_hour = f.sched_dep_hour
        WHERE w.temperature_c IS DISTINCT FROM f.temperature_c""")
    assert mismatches == 0


def test_cancelled_flights_have_reason(pipeline_data):
    assert q(pipeline_data, "SELECT COUNT(*) FROM fact_flights WHERE is_cancelled AND cancellation_reason IS NULL") == 0


def test_date_dimension_covers_period(pipeline_data):
    assert q(pipeline_data, "SELECT COUNT(*) FROM dim_date") == 31 + 29


def test_quality_checks_pass(pipeline_data):
    assert q(pipeline_data, "SELECT COUNT(*) FROM quality_checks WHERE NOT passed") == 0


def test_powerbi_exports(pipeline_data):
    names = {p.name for p in (pipeline_data / "powerbi").glob("*.parquet")}
    assert {"fact_flights.parquet", "dim_airport.parquet", "agg_daily.parquet"} <= names
    agg = pd.read_parquet(pipeline_data / "powerbi" / "agg_daily.parquet")
    assert agg["flights"].sum() == 800


def test_rerun_is_idempotent(pipeline_data):
    import extract_flights, build_warehouse
    extract_flights.run()
    build_warehouse.run()
    assert q(pipeline_data, "SELECT COUNT(*) FROM fact_flights") == 800


def test_sql_queries_run(pipeline_data, tmp_path):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("run_all", Path(__file__).parent.parent / "sql" / "run_all.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = mod.run(tmp_path / "r.md")
    text = out.read_text(encoding="utf-8")
    assert text.count("\n## ") == 9
