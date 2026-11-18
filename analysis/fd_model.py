"""Modèle de probabilité de retard (15 min ou plus à l'arrivée).

Seules des informations connues avant le départ sont utilisées : calendrier,
heure prévue, compagnie, liaison, et météo de l'aéroport de départ à l'heure
prévue (la météo observée sert ici d'approximation d'une prévision).

Évaluation honnête : on apprend sur le passé et on teste sur une période
postérieure jamais vue (découpage temporel, pas aléatoire).
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

CALENDAR = ["month", "weekday", "sched_dep_hour"]
ROUTE = ["carrier_code", "origin", "dest"]
NUMERIC_ROUTE = ["distance_miles"]
WEATHER_NUM = ["temperature_c", "precipitation_mm", "snowfall_cm", "wind_kmh", "gusts_kmh", "cloud_cover_pct"]
WEATHER_CAT = ["weather_condition"]
TARGET = "is_delayed"
MAX_CATEGORIES = 200

FEATURE_SETS = {
    "Calendrier": (CALENDAR, []),
    "Calendrier + compagnie et liaison": (CALENDAR + ROUTE, NUMERIC_ROUTE),
    "Tout, avec la météo": (CALENDAR + ROUTE + WEATHER_CAT, NUMERIC_ROUTE + WEATHER_NUM),
}


def prepare(df):
    """Vols non annulés, croisés avec la météo, colonnes au bon type."""
    d = df[~df["is_cancelled"] & df["weather_condition"].notna()].copy()
    d["flight_date"] = pd.to_datetime(d["flight_date"])
    d["month"] = d["flight_date"].dt.month
    d["weekday"] = d["flight_date"].dt.day_of_week + 1
    for c in ROUTE + WEATHER_CAT:
        d[c] = d[c].astype(str)
    # Le gradient boosting accepte au plus 255 modalités par variable : les aéroports
    # les moins fréquentés (une part infime des vols) sont regroupés dans « Autre ».
    for c in ("origin", "dest"):
        keep = d[c].value_counts().index[:MAX_CATEGORIES]
        d[c] = d[c].where(d[c].isin(keep), "Autre")
    d[TARGET] = d[TARGET].astype(int)
    return d


def temporal_split(d):
    """Test = les 12 derniers mois si la période dépasse 400 jours,
    sinon les 30 % les plus récents."""
    dates = d["flight_date"]
    span = (dates.max() - dates.min()).days
    cut = dates.max() - pd.Timedelta(days=365) if span > 400 else dates.quantile(0.7)
    return d[dates <= cut], d[dates > cut], cut


def _boosting(cats, nums):
    pre = ColumnTransformer([
        ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                               encoded_missing_value=-1), cats),
        ("num", "passthrough", nums),
    ])
    clf = HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.08, max_leaf_nodes=63,
        categorical_features=list(range(len(cats))), early_stopping=True,
        validation_fraction=0.1, random_state=0)
    return make_pipeline(pre, clf)


def _logistic(cats, nums):
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=200), cats),
        ("num", make_pipeline(StandardScaler()), nums),
    ])
    return make_pipeline(pre, LogisticRegression(max_iter=500, C=1.0))


def scores(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {
        "log_loss": log_loss(y, p, labels=[0, 1]),
        "brier": brier_score_loss(y, p),
        "auc": roc_auc_score(y, p) if len(set(y)) > 1 else np.nan,
        "pr_auc": average_precision_score(y, p),
    }


def evaluate(train, test):
    """Compare une référence naïve, une régression logistique et un gradient
    boosting, puis l'apport de chaque groupe de variables (ablation)."""
    y_tr, y_te = train[TARGET].values, test[TARGET].values
    rows = [{"modele": "Référence naïve (taux moyen)", "variables": "aucune",
             **scores(y_te, np.full(len(y_te), y_tr.mean()))}]
    fitted = {}
    for name, (cats, nums) in FEATURE_SETS.items():
        model = _boosting(cats, nums).fit(train[cats + nums], y_tr)
        p = model.predict_proba(test[cats + nums])[:, 1]
        rows.append({"modele": "Gradient boosting", "variables": name, **scores(y_te, p)})
        fitted[name] = (model, p)
    cats, nums = FEATURE_SETS["Tout, avec la météo"]
    logit = _logistic(cats, nums).fit(train[cats + nums], y_tr)
    rows.append({"modele": "Régression logistique", "variables": "Tout, avec la météo",
                 **scores(y_te, logit.predict_proba(test[cats + nums])[:, 1])})
    return pd.DataFrame(rows), fitted


def calibration(y, p, bins=10):
    """Taux de retard observé par tranche de probabilité prédite."""
    q = pd.qcut(p, bins, duplicates="drop")
    t = pd.DataFrame({"y": y, "p": p, "q": q}).groupby("q", observed=True)
    return t.agg(predit=("p", "mean"), observe=("y", "mean"), vols=("y", "size")).reset_index(drop=True)


def permutation_importance_groups(model, test, groups, metric=log_loss, seed=0):
    """Hausse de la log loss quand on mélange un groupe de variables :
    plus elle monte, plus le modèle s'appuie sur ce groupe."""
    rng = np.random.default_rng(seed)
    cats, nums = FEATURE_SETS["Tout, avec la météo"]
    X = test[cats + nums].copy()
    y = test[TARGET].values
    base = metric(y, model.predict_proba(X)[:, 1], labels=[0, 1])
    out = []
    for name, cols in groups.items():
        Xp = X.copy()
        idx = rng.permutation(len(Xp))
        Xp[cols] = Xp[cols].values[idx]
        out.append({"groupe": name,
                    "hausse_log_loss": metric(y, model.predict_proba(Xp)[:, 1], labels=[0, 1]) - base})
    return pd.DataFrame(out).sort_values("hausse_log_loss", ascending=False)


IMPORTANCE_GROUPS = {
    "Heure de départ": ["sched_dep_hour"],
    "Mois et jour": ["month", "weekday"],
    "Compagnie": ["carrier_code"],
    "Aéroports (départ, arrivée)": ["origin", "dest", "distance_miles"],
    "Météo au départ": WEATHER_CAT + WEATHER_NUM,
}
