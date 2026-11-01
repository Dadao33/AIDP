# %% [markdown]
# # BIC -- 04 Gold facts, scenario tools and policies
# Reload the model from a persisted table; no shared notebook session is assumed. Publish baseline portfolio facts only. Scenario calculations and candidate alternatives run in the agent Custom Code tools on request. No alternative or recommendation rows are generated here.

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
from shared.engine import evaluate
s=config["catalog"]["silver"];g=config["catalog"]["gold"]
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {g}")
model=json.loads(spark.table(s+".model_artifact").first()["model_json"])
cases=[r.asDict(recursive=True) for r in spark.table(s+".accounts").orderBy("id").collect()]
supply={r.case_id:r.asDict(recursive=True) for r in spark.table(s+".supply").collect()}
policy=spark.table(s+".policies").first().asDict(recursive=True)
# Spark infers a JSON object with account identifiers as a struct; Row.asDict above normalizes it.
current=[]
for c in cases:
    o=supply[c["id"]]
    x=evaluate(c,o,policy,model)
    current.append((c["id"],c["customer"],c["region_name"],c["product"],x["risk"],x["firm_shortfall"],x["peak_shortfall"],x["short_days"],json.dumps(x,ensure_ascii=False),config["batch_id"]))
def put(name,rows,schema):
    df=spark.createDataFrame(rows,schema)
    df.write.format("delta").mode("overwrite").saveAsTable(g+"."+name)
    return df
cur=put("account_context",current,"case_id string, customer string, region string, product string, risk double, firm_shortfall long, peak_shortfall long, short_days int, context_json string, batch_id string")
put("policies",[(r["id"],r["title"],r["owner"],r["requirement"],policy["version"],policy["effective_from"],policy["effective_to"]) for r in policy["rules"]],"policy_id string, title string, owner string, requirement string, policy_version string, effective_from string, effective_to string")
put("model_performance",[(model["version"],model["mlflow_run_id"],json.dumps(model["metrics"]),model["forecast_wape"],model["baseline_wape"])],"model_version string, mlflow_run_id string, metrics_json string, forecast_wape double, baseline_wape double")
budget={r.case_id:r.asDict() for r in spark.table(s+".budget").collect()}
finance=[]
for c in cases:
    x=evaluate(c,supply[c["id"]],policy,model)
    finance.append((c["id"],c["region_name"],float(budget[c["id"]]["budget_revenue"]),float(x["forecast_units"]*c["unit_price"]),float(x["forecast_units"]*c["unit_price"]*c["margin_rate"]),float(x["peak_shortfall"]*c["unit_price"]*c["margin_rate"])))
put("financial_outlook",finance,"case_id string, region string, revenue_budget double, forecast_revenue double, forecast_gross_margin double, peak_margin_exposure double")
assert cur.count()==26
assert cur.where("short_days>0").count()==4, "Investigate any change in the four baseline exception stories"
export=config["object_storage"]["gold_export_uri"].rstrip("/")
# Every export lands in Object Storage, not JDE. Coalesce is suitable only for this small demo.
cur.coalesce(1).write.mode("overwrite").json(export+"/accounts")
spark.createDataFrame([(json.dumps(model),)],"model_json string").coalesce(1).write.mode("overwrite").json(export+"/model")
print("Gold ready: 26 baseline accounts. Alternatives are calculated on demand by agent tools. Build and test the BIC policy Knowledge Base before agent deployment.")
