import pandas as pd
import numpy as np
from pathlib import Path
import pickle

DATA_DIR = Path(__file__).parent.parent / "data"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

FEATURE_COLS = [
    'total_parking_minutes', 'metar_temperature_c', 'metar_relative_humidity',
    'metar_dew_point_c', 'metar_wind_speed_kn', 'metar_visibility_mi',
    'metar_hour_precipitation', 'sea_salt_aerosol_003_05_mixing_ratio',
    'sea_salt_aerosol_05_5_mixing_ratio', 'sea_salt_aerosol_5_20_mixing_ratio',
    'dust_aerosol_003_055_mixing_ratio', 'dust_aerosol_055_09_mixing_ratio',
    'dust_aerosol_09_20_mixing_ratio', 'hydrophilic_organic_matter_aerosol_mixing_ratio',
    'hydrophobic_organic_matter_aerosol_mixing_ratio', 'hydrophilic_black_carbon_aerosol_mixing_ratio',
    'hydrophobic_black_carbon_aerosol_mixing_ratio', 'sulphate_aerosol_mixing_ratio',
    'ethane', 'c3h8', 'isoprene', 'carbon_monoxide_mass_mixing_ratio',
    'ozone_mass_mixing_ratio', 'h2o2', 'formaldehyde', 'hno3',
    'nitrogen_monoxide_mass_mixing_ratio', 'nitrogen_dioxide_mass_mixing_ratio',
    'oh', 'organic_nitrates', 'specific_humidity', 'sulphur_dioxide_mass_mixing_ratio',
    'temperature'
]

FEATURE_LABELS = {
    'total_parking_minutes': 'Temps de parking',
    'metar_temperature_c': 'Température (°C)',
    'metar_relative_humidity': 'Humidité relative (%)',
    'metar_dew_point_c': 'Point de rosée (°C)',
    'metar_wind_speed_kn': 'Vitesse du vent (kn)',
    'metar_visibility_mi': 'Visibilité (mi)',
    'metar_hour_precipitation': 'Précipitations',
    'sea_salt_aerosol_003_05_mixing_ratio': 'Sel marin (fin)',
    'sea_salt_aerosol_05_5_mixing_ratio': 'Sel marin (moyen)',
    'sea_salt_aerosol_5_20_mixing_ratio': 'Sel marin (grossier)',
    'dust_aerosol_003_055_mixing_ratio': 'Poussière (fin)',
    'dust_aerosol_055_09_mixing_ratio': 'Poussière (moyen)',
    'dust_aerosol_09_20_mixing_ratio': 'Poussière (grossier)',
    'hydrophilic_organic_matter_aerosol_mixing_ratio': 'Matière organique (hydrophile)',
    'hydrophobic_organic_matter_aerosol_mixing_ratio': 'Matière organique (hydrophobe)',
    'hydrophilic_black_carbon_aerosol_mixing_ratio': 'Carbone noir (hydrophile)',
    'hydrophobic_black_carbon_aerosol_mixing_ratio': 'Carbone noir (hydrophobe)',
    'sulphate_aerosol_mixing_ratio': 'Aérosol sulfaté',
    'ethane': 'Éthane',
    'c3h8': 'Propane (C3H8)',
    'isoprene': 'Isoprène',
    'carbon_monoxide_mass_mixing_ratio': 'Monoxyde de carbone',
    'ozone_mass_mixing_ratio': 'Ozone',
    'h2o2': 'H₂O₂',
    'formaldehyde': 'Formaldéhyde',
    'hno3': 'Acide nitrique (HNO₃)',
    'nitrogen_monoxide_mass_mixing_ratio': 'Monoxyde d\'azote',
    'nitrogen_dioxide_mass_mixing_ratio': 'Dioxyde d\'azote (NO₂)',
    'oh': 'Radical hydroxyle (OH)',
    'organic_nitrates': 'Nitrates organiques',
    'specific_humidity': 'Humidité spécifique',
    'sulphur_dioxide_mass_mixing_ratio': 'Dioxyde de soufre (SO₂)',
    'temperature': 'Température (K)',
}


def _build_training_data():
    env = pd.read_csv(DATA_DIR / "environment_training.csv")
    cor = pd.read_csv(DATA_DIR / "corrosions_training.csv")

    cor['obs_dt'] = pd.to_datetime(cor['observation_date'])
    cor['obs_month'] = cor['obs_dt'].dt.to_period('M').astype(str)
    cor['early_dt'] = cor['obs_dt'] - pd.DateOffset(months=24)
    cor['early_month'] = cor['early_dt'].dt.to_period('M').astype(str)

    labels = []
    for _, row in cor.iterrows():
        labels.append({'aircraft_id': row['aircraft_id'], 'year_month': row['obs_month'], 'label': 1})
        labels.append({'aircraft_id': row['aircraft_id'], 'year_month': row['early_month'], 'label': 0})

    labels_df = pd.DataFrame(labels)
    merged = labels_df.merge(env, on=['aircraft_id', 'year_month'], how='inner')

    X = merged[FEATURE_COLS].fillna(merged[FEATURE_COLS].median())
    y = merged['label']
    return X, y


def load_or_train_model():
    model_path = CACHE_DIR / "model.pkl"
    if model_path.exists():
        with open(model_path, 'rb') as f:
            return pickle.load(f)

    from xgboost import XGBClassifier
    X, y = _build_training_data()
    model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        random_state=42, eval_metric='logloss', verbosity=0
    )
    model.fit(X, y)

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    return model


def get_predictions():
    pred_path = CACHE_DIR / "predictions.csv"
    if pred_path.exists():
        return pd.read_csv(pred_path)

    model = load_or_train_model()
    test = pd.read_csv(DATA_DIR / "environment_test.csv")
    X_test = test[FEATURE_COLS].fillna(test[FEATURE_COLS].median())
    test['corrosion_risk'] = model.predict_proba(X_test)[:, 1]
    test['id'] = test['aircraft_id'] + '_' + test['year_month']
    test.to_csv(pred_path, index=False)
    return test


def predict_single(features_dict):
    model = load_or_train_model()
    row = {col: features_dict.get(col, 0) for col in FEATURE_COLS}
    X = pd.DataFrame([row])
    return float(model.predict_proba(X)[0, 1])


def get_feature_importance():
    model = load_or_train_model()
    return pd.DataFrame({
        'feature': FEATURE_COLS,
        'label': [FEATURE_LABELS.get(c, c) for c in FEATURE_COLS],
        'importance': model.feature_importances_,
    }).sort_values('importance', ascending=False).reset_index(drop=True)


def get_corrosion_events():
    cor = pd.read_csv(DATA_DIR / "corrosions_training.csv", parse_dates=['observation_date'])
    cor = cor.sort_values('observation_date').reset_index(drop=True)
    cor['n'] = range(1, len(cor) + 1)
    cor['year'] = cor['observation_date'].dt.year
    return cor


def get_fleet_summary():
    preds = get_predictions()
    summary = preds.groupby('aircraft_id').agg(
        max_risk=('corrosion_risk', 'max'),
        mean_risk=('corrosion_risk', 'mean'),
        months=('year_month', 'count'),
        last_month=('year_month', 'max'),
    ).reset_index()
    summary['risk_level'] = pd.cut(
        summary['max_risk'],
        bins=[0, 0.4, 0.7, 1.0],
        labels=['Low', 'Medium', 'High']
    )
    return summary
