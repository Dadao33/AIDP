# %% [markdown]
# # BIC Retail Studio -- 01 Raw to Bronze
# All source files are in OCI Object Storage. JDE is not connected. No passwords or keys are embedded. Run in the BIC workspace on the selected Spark cluster.

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
raw=config["object_storage"]["raw_uri"].rstrip("/")
assert "<" not in raw and raw.startswith("oci://"), "Bind the real bucket and namespace first"
b=config["catalog"]["bronze"]
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {b}")
for table,filename in [("accounts","accounts.json"),("supply","supply.json"),("policies","policies.json")]:
    frame=spark.read.option("multiLine",True).json(raw+"/"+filename)
    assert frame.count()>0, filename
    frame.withColumn("_ingested_at",F.current_timestamp()).withColumn("_source",F.lit(raw+"/"+filename)).write.format("delta").mode("overwrite").saveAsTable(b+"."+table)
budget=spark.read.option("multiLine",True).json(raw+"/budget.json").select(F.explode("budget").alias("b")).select("b.*")
budget.write.format("delta").mode("overwrite").saveAsTable(b+".budget")
history=spark.read.option("header",True).option("inferSchema",True).csv(raw+"/historical_snapshots.csv")
assert history.count()==8064, "Unexpected historical row count"
history.withColumn("_source",F.lit(raw+"/historical_snapshots.csv")).write.format("delta").mode("overwrite").saveAsTable(b+".history")
print("Bronze complete: source facts only; no precomputed risk scores or action recommendations")
