# %% [markdown]
# # Athlete Readiness - 03 ML et MLOps
#
# Comparaison de trois modeles scikit-learn, evaluation temporelle, calibration et journalisation MLflow.

# %%
from pathlib import Path
import json
import tempfile

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, precision_recall_curve, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# %%
CONFIG_PATH = Path("/Workspace/Config/athlete_readiness_config.json")
if not CONFIG_PATH.exists():
    CONFIG_PATH = Path("../config/athlete_readiness_config.json")
config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

source = f"{config['catalog']['silver_catalog']}.{config['catalog']['silver_schema']}.athlete_features_daily"
cutoff = pd.Timestamp(config["ml"]["training_cutoff_date"])
seed = config["ml"]["random_seed"]

numeric_features = [
    "sleep_hours", "sleep_quality_1_10", "soreness_1_10", "stress_1_10", "mood_1_10",
    "fatigue_declared_1_10", "hrv_delta_pct", "resting_hr_delta", "sleep_delta_hours",
    "acute_load_7d", "chronic_load_28d", "acute_chronic_ratio", "high_speed_7d",
    "sprint_count_7d", "travel_hours", "minutes_played", "prior_injury_count", "days_since_last_injury",
]
categorical_features = ["position", "event_type", "surface"]
feature_columns = numeric_features + categorical_features

pdf = spark.table(source).select("athlete_id", "observation_date", "injury_next_7d", *feature_columns).toPandas()
pdf["observation_date"] = pd.to_datetime(pdf["observation_date"])
pdf = pdf.dropna(subset=["observation_date", "injury_next_7d"])

train = pdf[pdf["observation_date"] < cutoff].copy()
test = pdf[pdf["observation_date"] >= cutoff].copy()
X_train, y_train = train[feature_columns], train["injury_next_7d"].astype(int)
X_test, y_test = test[feature_columns], test["injury_next_7d"].astype(int)

print(f"Train: {len(train):,} lignes - positifs {y_train.sum():,}")
print(f"Test : {len(test):,} lignes - positifs {y_test.sum():,}")

# %%
preprocessor = ColumnTransformer([
    ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric_features),
    ("category", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical_features),
])

candidates = {
    "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed),
    "random_forest": RandomForestClassifier(n_estimators=240, min_samples_leaf=6, class_weight="balanced_subsample", random_state=seed, n_jobs=-1),
    "gradient_boosting": GradientBoostingClassifier(n_estimators=160, max_depth=2, learning_rate=0.045, random_state=seed),
}
business_model_names = {
    "logistic_regression": "Régression logistique calibrée",
    "random_forest": "Forêt aléatoire calibrée",
    "gradient_boosting": "Gradient boosting calibré",
}


def metrics_for(y_true, probability):
    precision, recall, thresholds = precision_recall_curve(y_true, probability)
    f2 = 5 * precision * recall / np.maximum(4 * precision + recall, 1e-9)
    best_index = int(np.nanargmax(f2))
    threshold = float(thresholds[min(best_index, len(thresholds) - 1)])
    predicted = probability >= threshold
    return {
        "roc_auc": float(roc_auc_score(y_true, probability)),
        "pr_auc": float(average_precision_score(y_true, probability)),
        "brier": float(brier_score_loss(y_true, probability)),
        "threshold_f2": threshold,
        "recall_at_threshold": float(((predicted == 1) & (y_true.to_numpy() == 1)).sum() / max((y_true == 1).sum(), 1)),
        "precision_at_threshold": float(((predicted == 1) & (y_true.to_numpy() == 1)).sum() / max(predicted.sum(), 1)),
    }

# %% [markdown]
# ## Experiment tracking AIDP MLOps

# %%
experiment_name = config["ml"]["experiment_name"]
mlflow.set_experiment(experiment_name)
results = []
fitted = {}

for model_name, estimator in candidates.items():
    base_pipeline = Pipeline([("features", preprocessor), ("model", estimator)])
    pipeline = CalibratedClassifierCV(base_pipeline, method="sigmoid", cv=3)
    with mlflow.start_run(run_name=model_name):
        pipeline.fit(X_train, y_train)
        probability = pipeline.predict_proba(X_test)[:, 1]
        model_metrics = metrics_for(y_test, probability)
        mlflow.log_params({"model": model_name, "prediction_horizon_days": config["ml"]["prediction_horizon_days"], "training_cutoff": str(cutoff.date())})
        mlflow.log_metrics(model_metrics)
        results.append({"model_name": model_name, **model_metrics})
        fitted[model_name] = pipeline

results_df = pd.DataFrame(results).sort_values(["pr_auc", "brier"], ascending=[False, True])
display(results_df)

# %%
champion_name = results_df.iloc[0]["model_name"]
champion = fitted[champion_name]
champion_metrics = results_df.iloc[0].to_dict()
champion_business_name = business_model_names[champion_name]

with mlflow.start_run(run_name=f"champion_{champion_name}") as run:
    mlflow.log_params({"champion_model": champion_name, "feature_count": len(feature_columns)})
    mlflow.log_metrics({k: float(v) for k, v in champion_metrics.items() if k != "model_name"})
    with tempfile.TemporaryDirectory() as temp_dir:
        model_path = Path(temp_dir) / "athlete_readiness_model.joblib"
        joblib.dump(champion, model_path)
        mlflow.log_artifact(str(model_path), artifact_path="model")
    mlflow.sklearn.log_model(
        champion,
        artifact_path="registered_model",
        registered_model_name=config["ml"]["registered_model_name"],
    )
    champion_run_id = run.info.run_id

print(f"Champion métier : {champion_business_name}")
print(f"Identifiant technique : {champion_name} - run_id={champion_run_id}")
print("Critère de sélection : PR-AUC décroissante, puis score de Brier croissant.")
print("La ROC-AUC mesure la discrimination globale ; elle n'est pas le risque individuel affiché pour un sportif.")

# %% [markdown]
# L'enregistrement dans le registre AIDP peut etre finalise depuis l'interface MLOps avec le run ci-dessus.
# La promotion en Production reste une action explicite et gouvernee.

# %%
metrics_spark = spark.createDataFrame(results_df)
metrics_spark.write.mode("overwrite").saveAsTable(
    f"{config['catalog']['silver_catalog']}.{config['catalog']['silver_schema']}.ml_model_performance"
)

# Le pipeline serialise est garde en memoire pour le notebook Gold si execute dans la meme session.
ATHLETE_READINESS_MODEL = champion
ATHLETE_READINESS_THRESHOLD = float(champion_metrics["threshold_f2"])
ATHLETE_READINESS_FEATURES = feature_columns
ATHLETE_READINESS_RUN_ID = champion_run_id
