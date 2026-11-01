# %% [markdown]
# # BIC -- 03 Forecasting and service-risk scoring
# Logistic regression estimates the probability of an incomplete order line in seven days. Log-linear regression forecasts weekly units. A chronological training/validation/test split prevents future-label leakage; the decision threshold is chosen on validation only. Metrics are measured on synthetic outcomes and do not establish BIC production performance.

# %%
from pathlib import Path
import sys, json, os, re
ROOT=Path(os.environ.get("BIC_WORKSPACE_ROOT", "/Workspace/BICDemo"))
sys.path.insert(0,str(ROOT))
config=json.loads((ROOT/"config/demo.json").read_text())
for name in config["catalog"].values():
    assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*",name), name
from pyspark.sql import functions as F


# %%
from shared.ml import train
from shared.engine import fingerprint
import mlflow
s=config["catalog"]["silver"]
rows=[r.asDict() for r in spark.table(s+".history").orderBy("snapshot_date","cohort_id").collect()]
model=train(rows)
mlflow.set_experiment(config["mlflow"]["experiment"])
with mlflow.start_run(run_name=config["batch_id"]) as run:
    mlflow.log_params({"risk_algorithm":"standardized_logistic_regression","forecast_algorithm":"log_linear_regression","split":"60/12/12 weeks","threshold_selection":"validation F1","data_kind":"synthetic","feature_count":5})
    mlflow.log_metrics({"test_roc_auc":model["metrics"]["roc_auc"],"test_brier":model["metrics"]["brier"],"test_precision":model["metrics"]["precision"],"test_recall":model["metrics"]["recall"],"forecast_wape":model["forecast_wape"],"baseline_wape":model["baseline_wape"],"threshold":model["threshold"]})
    mlflow.log_dict(model,"model.json")
    model["mlflow_run_id"]=run.info.run_id
    mlflow.set_tag("serving_contract","shared.engine.score + model.json")
model["version"]="bic-service-risk-v2"
spark.createDataFrame([(config["batch_id"],json.dumps(model))],"batch_id string, model_json string").write.format("delta").mode("overwrite").saveAsTable(s+".model_artifact")
print(json.dumps({"run_id":model["mlflow_run_id"],"test":model["metrics"],"forecast_wape":model["forecast_wape"],"baseline_wape":model["baseline_wape"]},indent=2))
