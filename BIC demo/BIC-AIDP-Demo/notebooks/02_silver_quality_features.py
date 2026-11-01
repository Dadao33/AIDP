# %% [markdown]
# # BIC -- 02 Data quality and point-in-time features
# One account scenario per regional distributor and SKU. Donor pools are independent scenario fixtures, not a jointly allocatable national stock. Historical labels describe the following seven days and are excluded from model inputs.

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
b=config["catalog"]["bronze"];s=config["catalog"]["silver"]
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {s}")
accounts=spark.table(b+".accounts").drop("_source","_ingested_at")
supply=spark.table(b+".supply").drop("_source","_ingested_at")
assert accounts.count()==accounts.select("id").distinct().count()==26
assert supply.count()==supply.select("case_id").distinct().count()==26
assert accounts.join(supply,accounts.id==supply.case_id,"left_anti").count()==0
assert supply.where("allocated_units < 0 OR receipt_units < 0 OR donor_physical_units < donor_committed_units + donor_safety_units").count()==0
history=spark.table(b+".history").drop("_source")
assert history.select("snapshot_date","cohort_id").distinct().count()==history.count()
assert history.where("not_served_7d NOT IN (0,1) OR demand_next_7d < 0 OR daily_units_28d <= 0").count()==0
assert history.where(F.date_add(F.to_date("snapshot_date"),7)>=F.lit(config["demo"]["as_of"])).count()==0
bounds={r["split"]:r.asDict() for r in history.groupBy("split").agg(F.min("snapshot_date").alias("first"),F.max("snapshot_date").alias("last")).collect()}
assert bounds["train"]["last"] < bounds["validation"]["first"] < bounds["test"]["first"]
for name,frame in [("accounts",accounts),("supply",supply),("history",history),("budget",spark.table(b+".budget")),("policies",spark.table(b+".policies").drop("_source","_ingested_at"))]:
    frame.write.format("delta").mode("overwrite").saveAsTable(s+"."+name)
print("PASS: uniqueness, referential integrity, stock arithmetic, chronological labels")
