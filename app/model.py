import pandas as pd
import numpy as np
from pathlib import Path
import pickle

DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

FEATURE_COLS = [
    "total_parking_minutes",
    "metar_temperature_c",
    "metar_relative_humidity",
    "metar_dew_point_c",
    "metar_wind_speed_kn",
    "metar_visibility_mi",
    "metar_hour_precipitation",
    "sea_salt_aerosol_003_05_mixing_ratio",
    "sea_salt_aerosol_05_5_mixing_ratio",
    "sea_salt_aerosol_5_20_mixing_ratio",
    "dust_aerosol_003_055_mixing_ratio",
    "dust_aerosol_055_09_mixing_ratio",
    "dust_aerosol_09_20_mixing_ratio",
    "hydrophilic_organic_matter_aerosol_mixing_ratio",
    "hydrophobic_organic_matter_aerosol_mixing_ratio",
    "hydrophilic_black_carbon_aerosol_mixing_ratio",
    "hydrophobic_black_carbon_aerosol_mixing_ratio",
    "sulphate_aerosol_mixing_ratio",
    "ethane",
    "c3h8",
    "isoprene",
    "carbon_monoxide_mass_mixing_ratio",
    "ozone_mass_mixing_ratio",
    "h2o2",
    "formaldehyde",
    "hno3",
    "nitrogen_monoxide_mass_mixing_ratio",
    "nitrogen_dioxide_mass_mixing_ratio",
    "oh",
    "organic_nitrates",
    "specific_humidity",
    "sulphur_dioxide_mass_mixing_ratio",
    "temperature",
]

FEATURE_LABELS = {
    "total_parking_minutes": "Temps de parking",
    "metar_temperature_c": "Température (°C)",
    "metar_relative_humidity": "Humidité relative (%)",
    "metar_dew_point_c": "Point de rosée (°C)",
    "metar_wind_speed_kn": "Vitesse du vent (kn)",
    "metar_visibility_mi": "Visibilité (mi)",
    "metar_hour_precipitation": "Précipitations",
    "sea_salt_aerosol_003_05_mixing_ratio": "Sel marin (fin)",
    "sea_salt_aerosol_05_5_mixing_ratio": "Sel marin (moyen)",
    "sea_salt_aerosol_5_20_mixing_ratio": "Sel marin (grossier)",
    "dust_aerosol_003_055_mixing_ratio": "Poussière (fin)",
    "dust_aerosol_055_09_mixing_ratio": "Poussière (moyen)",
    "dust_aerosol_09_20_mixing_ratio": "Poussière (grossier)",
    "hydrophilic_organic_matter_aerosol_mixing_ratio": "Matière organique (hydrophile)",
    "hydrophobic_organic_matter_aerosol_mixing_ratio": "Matière organique (hydrophobe)",
    "hydrophilic_black_carbon_aerosol_mixing_ratio": "Carbone noir (hydrophile)",
    "hydrophobic_black_carbon_aerosol_mixing_ratio": "Carbone noir (hydrophobe)",
    "sulphate_aerosol_mixing_ratio": "Aérosol sulfaté",
    "ethane": "Éthane",
    "c3h8": "Propane (C3H8)",
    "isoprene": "Isoprène",
    "carbon_monoxide_mass_mixing_ratio": "Monoxyde de carbone",
    "ozone_mass_mixing_ratio": "Ozone",
    "h2o2": "H₂O₂",
    "formaldehyde": "Formaldéhyde",
    "hno3": "Acide nitrique (HNO₃)",
    "nitrogen_monoxide_mass_mixing_ratio": "Monoxyde d'azote",
    "nitrogen_dioxide_mass_mixing_ratio": "Dioxyde d'azote (NO₂)",
    "oh": "Radical hydroxyle (OH)",
    "organic_nitrates": "Nitrates organiques",
    "specific_humidity": "Humidité spécifique",
    "sulphur_dioxide_mass_mixing_ratio": "Dioxyde de soufre (SO₂)",
    "temperature": "Température (K)",
}


def _build_training_data():
    env = pd.read_csv(DATA_DIR / "environment_training.csv")
    cor = pd.read_csv(DATA_DIR / "corrosions_training.csv")

    cor["obs_dt"] = pd.to_datetime(cor["observation_date"])
    cor["obs_month"] = cor["obs_dt"].dt.to_period("M").astype(str)
    cor["early_dt"] = cor["obs_dt"] - pd.DateOffset(months=24)
    cor["early_month"] = cor["early_dt"].dt.to_period("M").astype(str)

    labels = []
    for _, row in cor.iterrows():
        labels.append(
            {
                "aircraft_id": row["aircraft_id"],
                "year_month": row["obs_month"],
                "label": 1,
            }
        )
        labels.append(
            {
                "aircraft_id": row["aircraft_id"],
                "year_month": row["early_month"],
                "label": 0,
            }
        )

    labels_df = pd.DataFrame(labels)
    merged = labels_df.merge(env, on=["aircraft_id", "year_month"], how="inner")

    X = merged[FEATURE_COLS].fillna(merged[FEATURE_COLS].median())
    y = merged["label"]
    return X, y


# --- Adaptateur pour le modèle d'ensemble livré par l'équipe ML ---------------
# model.pkl contient un dict : {'lgb_models': [5 LGBMClassifier],
# 'xgb_models': [3 XGBClassifier], 'features': [40 features dérivées], 'brier_cv': float}

# Le simulateur n'a pas l'historique réel d'un scénario hypothétique : on suppose
# des conditions constantes sur cette durée pour reconstruire les features cumulées.
SIM_HISTORY_MONTHS = 24

_SUFFIX_LABELS = {
    "now": "mois courant",
    "cumsum": "cumul",
    "cummean": "moyenne cumulée",
    "cummax": "max cumulé",
    "cumstd": "variabilité cumulée",
}

_ENGINEERED_LABELS = {
    "ground_to_flight_ratio": "Ratio temps au sol / vol",
    "parking_x_salt_cumsum": "Parking × sel marin (cumul)",
    "salt_x_humid_cumsum": "Sel marin × humidité (cumul)",
}


def engineered_label(feat):
    if feat in _ENGINEERED_LABELS:
        return _ENGINEERED_LABELS[feat]
    stem, _, suffix = feat.rpartition("_")
    if suffix in _SUFFIX_LABELS and stem in FEATURE_LABELS:
        return f"{FEATURE_LABELS[stem]} — {_SUFFIX_LABELS[suffix]}"
    return FEATURE_LABELS.get(feat, feat)


class CorrosionEnsemble:
    """Interface sklearn (predict_proba / feature_importances_) au-dessus de
    l'ensemble de l'équipe ML : moyenne des probabilités des 8 modèles."""

    def __init__(self, bundle):
        self.models = list(bundle["lgb_models"]) + list(bundle["xgb_models"])
        self.features = list(bundle["features"])
        self.brier_cv = float(bundle.get("brier_cv", float("nan")))

    def predict_proba(self, X):
        X = X[self.features]
        p = np.mean([m.predict_proba(X)[:, 1] for m in self.models], axis=0)
        return np.column_stack([1 - p, p])

    @property
    def feature_importances_(self):
        norm = []
        for m in self.models:
            imp = np.asarray(m.feature_importances_, dtype=float)
            total = imp.sum()
            norm.append(imp / total if total else imp)
        return np.mean(norm, axis=0)


def _engineer_steady_state(base, features, months=SIM_HISTORY_MONTHS):
    """Reconstruit les 40 features dérivées (_now / _cumsum / _cummean / _cummax /
    _cumstd + interactions) pour un scénario unique du simulateur, en supposant
    les conditions constantes sur `months` mois (cumstd vaut alors 0)."""
    vals = {}
    for k, v in base.items():
        vals[k] = 0.0 if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)
    if not vals.get("temperature"):
        vals["temperature"] = vals.get("metar_temperature_c", 15.0) + 273.15
    salt = vals.get("sea_salt_aerosol_5_20_mixing_ratio", 0.0)

    row = {}
    for f in features:
        if f == "ground_to_flight_ratio":
            row[f] = vals.get("total_parking_minutes", 0.0) / 44640
        elif f == "parking_x_salt_cumsum":
            row[f] = vals.get("total_parking_minutes", 0.0) * salt * months
        elif f == "salt_x_humid_cumsum":
            row[f] = salt * vals.get("metar_relative_humidity", 0.0) * months
        else:
            stem, _, suffix = f.rpartition("_")
            v = vals.get(stem, 0.0)
            row[f] = {
                "now": v,
                "cumsum": v * months,
                "cummean": v,
                "cummax": v,
                "cumstd": 0.0,
            }[suffix]
    return row


_MODEL_CACHE = None


def load_or_train_model():
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    model_path = CACHE_DIR / "model.pkl"
    if model_path.exists():
        with open(model_path, "rb") as f:
            obj = pickle.load(f)
        if isinstance(obj, dict) and "features" in obj:
            obj = CorrosionEnsemble(obj)
        _MODEL_CACHE = obj
        return obj

    from xgboost import XGBClassifier

    X, y = _build_training_data()
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss",
        verbosity=0,
    )
    model.fit(X, y)

    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    _MODEL_CACHE = model
    return model


def get_predictions():
    pred_path = CACHE_DIR / "predictions.csv"

    # Priorité 1 : vraies prédictions fournies (format id,corrosion_risk),
    # régénérées seulement si plus récentes que le cache
    real_path = DATA_DIR / "submission_clean.csv"
    if real_path.exists() and (
        not pred_path.exists()
        or real_path.stat().st_mtime > pred_path.stat().st_mtime
    ):
        raw = pd.read_csv(real_path)
        if list(raw.columns) == ["id", "corrosion_risk"]:
            # Reconstruire aircraft_id et year_month depuis l'id
            raw["aircraft_id"] = raw["id"].str.extract(r"^(.+)_(\d{4}-\d{2})$")[0]
            raw["year_month"] = raw["id"].str.extract(r"^(.+)_(\d{4}-\d{2})$")[1]
            # Joindre avec les colonnes environnementales du jeu test
            env_test = pd.read_csv(DATA_DIR / "environment_test.csv")
            merged = raw.merge(env_test, on=["aircraft_id", "year_month"], how="left")
            merged.to_csv(pred_path, index=False)
            return merged

    # Priorité 2 : cache déjà généré
    if pred_path.exists():
        return pd.read_csv(pred_path)

    # Priorité 3 : entraîner le modèle à la volée
    model = load_or_train_model()
    test = pd.read_csv(DATA_DIR / "environment_test.csv")
    X_test = test[FEATURE_COLS].fillna(test[FEATURE_COLS].median())
    test["corrosion_risk"] = model.predict_proba(X_test)[:, 1]
    test["id"] = test["aircraft_id"] + "_" + test["year_month"]
    test.to_csv(pred_path, index=False)
    return test


def predict_single(features_dict):
    model = load_or_train_model()
    if isinstance(model, CorrosionEnsemble):
        row = _engineer_steady_state(features_dict, model.features)
    else:
        row = {col: features_dict.get(col, 0) for col in FEATURE_COLS}
    X = pd.DataFrame([row])
    return float(model.predict_proba(X)[0, 1])


def get_feature_importance():
    model = load_or_train_model()
    feats = list(getattr(model, "features", FEATURE_COLS))
    return (
        pd.DataFrame(
            {
                "feature": feats,
                "label": [engineered_label(c) for c in feats],
                "importance": model.feature_importances_,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


_DISCRIMINANT_FEATS = [
    "metar_temperature_c",
    "metar_relative_humidity",
    "metar_dew_point_c",
    "metar_wind_speed_kn",
    "metar_visibility_mi",
    "metar_hour_precipitation",
    "total_parking_minutes",
    "sea_salt_aerosol_003_05_mixing_ratio",
    "sea_salt_aerosol_05_5_mixing_ratio",
    "sulphate_aerosol_mixing_ratio",
    "sulphur_dioxide_mass_mixing_ratio",
    "nitrogen_dioxide_mass_mixing_ratio",
    "ozone_mass_mixing_ratio",
    "specific_humidity",
    "temperature",
]


def get_discriminant_factors(n=15):
    env = pd.read_csv(DATA_DIR / "environment_training.csv")
    cor = pd.read_csv(
        DATA_DIR / "corrosions_training.csv", parse_dates=["observation_date"]
    )

    cor["delivery_date"] = pd.to_datetime(
        cor["aircraft_delivery_year"].astype(str)
        + "-"
        + cor["aircraft_delivery_month"].astype(str).str.zfill(2)
        + "-01"
    )
    cor["age_months"] = (
        (cor["observation_date"] - cor["delivery_date"]).dt.days / 30
    ).round(1)
    cor["ym_int"] = (
        cor["observation_date"].dt.strftime("%Y-%m").str.replace("-", "").astype(int)
    )

    env["ym_int"] = env["year_month"].str.replace("-", "").astype(int)

    parts = []
    for ac_id, ac_cor in cor.groupby("aircraft_id"):
        ac_env = env[env["aircraft_id"] == ac_id].sort_values("ym_int")
        if len(ac_env) == 0:
            continue
        m = pd.merge_asof(
            ac_cor.sort_values("ym_int"),
            ac_env.drop(columns=["aircraft_id"]),
            on="ym_int",
            direction="nearest",
        )
        parts.append(m)

    if not parts:
        return pd.DataFrame()

    final = pd.concat(parts, ignore_index=True)
    median_age = cor["age_months"].median()
    final["group"] = (final["age_months"] < median_age).map(
        {True: "précoce", False: "tardive"}
    )

    ref_mean = env[_DISCRIMINANT_FEATS].mean()
    ref_std = env[_DISCRIMINANT_FEATS].std().replace(0, 1)

    pre_dev = (
        final[final["group"] == "précoce"][_DISCRIMINANT_FEATS].mean() - ref_mean
    ) / ref_std
    tard_dev = (
        final[final["group"] == "tardive"][_DISCRIMINANT_FEATS].mean() - ref_mean
    ) / ref_std

    df = pd.DataFrame(
        {
            "feature": _DISCRIMINANT_FEATS,
            "label": [FEATURE_LABELS.get(f, f) for f in _DISCRIMINANT_FEATS],
            "précoce": pre_dev.values,
            "tardive": tard_dev.values,
        }
    )
    df["disc"] = (df["précoce"] - df["tardive"]).abs()
    return df.sort_values("disc", ascending=True).tail(n).reset_index(drop=True)


def get_corrosion_events():
    cor = pd.read_csv(
        DATA_DIR / "corrosions_training.csv", parse_dates=["observation_date"]
    )
    cor = cor.sort_values("observation_date").reset_index(drop=True)
    cor["n"] = range(1, len(cor) + 1)
    cor["year"] = cor["observation_date"].dt.year
    return cor


# Causes connues neutralisées dans l'analyse des facteurs de corrosion précoce,
# afin d'isoler les effets indépendants des autres expositions.
ANALYSIS_CONTROLS = [
    "sea_salt_aerosol_05_5_mixing_ratio",
    "metar_relative_humidity",
    "total_parking_minutes",
]


def get_corrosion_age_exposure():
    """Par appareil corrodé : âge au premier constat + exposition moyenne sur sa vie observée."""
    path = CACHE_DIR / "analysis_age_exposure.csv"
    if path.exists():
        return pd.read_csv(path)

    env = pd.read_csv(DATA_DIR / "environment_training.csv")
    first = get_corrosion_events().groupby("aircraft_id").first().reset_index()
    first["age_y"] = (
        first["observation_date"].dt.year
        + first["observation_date"].dt.month / 12
        - first["aircraft_delivery_year"]
        - first["aircraft_delivery_month"] / 12
    )
    expo = env.groupby("aircraft_id")[FEATURE_COLS].mean().reset_index()
    merged = first[["aircraft_id", "age_y"]].merge(expo, on="aircraft_id")
    merged[FEATURE_COLS] = merged[FEATURE_COLS].fillna(merged[FEATURE_COLS].median())
    merged.to_csv(path, index=False)
    return merged


def get_partial_correlations():
    """Corrélation de chaque exposition avec l'âge au premier constat de corrosion,
    après résidualisation des causes connues (sel marin, humidité, temps au sol)."""
    path = CACHE_DIR / "analysis_partial_corr.csv"
    if path.exists():
        return pd.read_csv(path)

    m = get_corrosion_age_exposure()
    A = np.column_stack(
        [np.ones(len(m))] + [m[c].values for c in ANALYSIS_CONTROLS]
    )

    def resid(v):
        beta, *_ = np.linalg.lstsq(A, v, rcond=None)
        return v - A @ beta

    ry = resid(m["age_y"].values.astype(float))
    n = len(m)
    rows = []
    for c in FEATURE_COLS:
        if c in ANALYSIS_CONTROLS:
            continue
        r = np.corrcoef(ry, resid(m[c].values.astype(float)))[0, 1]
        t = r * np.sqrt((n - 2) / (1 - r**2))
        rows.append(
            {"feature": c, "label": FEATURE_LABELS.get(c, c), "r_partial": r, "t": t}
        )
    out = pd.DataFrame(rows).sort_values("r_partial")
    out.to_csv(path, index=False)
    return out


def get_fleet_summary():
    preds = get_predictions()
    summary = (
        preds.groupby("aircraft_id")
        .agg(
            max_risk=("corrosion_risk", "max"),
            mean_risk=("corrosion_risk", "mean"),
            months=("year_month", "count"),
            last_month=("year_month", "max"),
        )
        .reset_index()
    )
    summary["risk_level"] = pd.cut(
        summary["max_risk"], bins=[0, 0.4, 0.7, 1.0], labels=["Low", "Medium", "High"]
    )
    return summary
