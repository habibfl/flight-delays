"""Le modèle tourne sur l'entrepôt simulé et respecte le découpage temporel."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))


def test_temporal_split_and_scores(pipeline_data):
    import fd_data, fd_model
    raw = fd_data.query("SELECT * FROM fact_flights")
    data = fd_model.prepare(raw)
    assert not data["is_cancelled"].any()
    train, test, cut = fd_model.temporal_split(data)
    assert train["flight_date"].max() <= cut < test["flight_date"].min()
    results, fitted = fd_model.evaluate(train, test)
    assert len(results) == 5
    assert results["log_loss"].notna().all()
    model, p = fitted["Tout, avec la météo"]
    assert ((p > 0) & (p < 1)).all()
    cal = fd_model.calibration(test["is_delayed"].values, p, bins=4)
    assert np.isclose(cal["vols"].sum(), len(test))
    imp = fd_model.permutation_importance_groups(model, test, fd_model.IMPORTANCE_GROUPS)
    assert set(imp["groupe"]) == set(fd_model.IMPORTANCE_GROUPS)


def test_rare_airports_grouped():
    import pandas as pd
    import fd_model
    n = 1000
    df = pd.DataFrame({
        "flight_date": pd.date_range("2024-01-01", periods=n, freq="h"),
        "is_cancelled": False, "is_delayed": [i % 3 == 0 for i in range(n)],
        "weather_condition": "Dégagé", "carrier_code": "AA",
        "origin": [f"A{i}" for i in range(n)], "dest": "ATL",
    })
    d = fd_model.prepare(df)
    assert d["origin"].nunique() <= fd_model.MAX_CATEGORIES + 1
