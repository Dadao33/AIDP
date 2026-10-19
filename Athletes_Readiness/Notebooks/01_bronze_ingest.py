# %% [markdown]
# # Athlete Readiness - 01 Bronze
#
# Ingestion fidele des observations depuis OCI Object Storage. Aucun score, aucune decision.

# %%
from pathlib import Path
import json

from pyspark.sql import functions as F

# %%
CONFIG_PATH = Path("/Workspace/Config/athlete_readiness_config.json")
if not CONFIG_PATH.exists():
    CONFIG_PATH = Path("../config/athlete_readiness_config.json")

config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
raw_uri = config["object_storage"]["raw_uri"].rstrip("/")
bronze_uri = config["object_storage"]["bronze_uri"].rstrip("/")
batch_id = config["runtime"]["batch_id"]

bronze_catalog = config["catalog"]["bronze_catalog"]
bronze_schema = config["catalog"]["bronze_schema"]
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {bronze_catalog}.{bronze_schema}")

print(f"Source Object Storage : {raw_uri}")
print(f"Cible Bronze         : {bronze_catalog}.{bronze_schema}")

# %%
CSV_SOURCES = {
    "athletes": "athletes.csv",
    "competition_calendar": "competition_calendar.csv",
    "daily_wellness": "daily_wellness.csv",
    "training_load": "training_load.csv",
    "nutrition_tracking": "nutrition_tracking.csv",
    "wearable_recovery": "wearable_recovery.csv",
    "injury_events": "injury_events.csv",
}

JSON_SOURCES = {
    "athlete_declarations": "athlete_declarations.jsonl",
    "medical_visits": "medical_visits.jsonl",
}


def add_lineage(df, source_name: str):
    return (
        df.withColumn("_aidp_source", F.lit(source_name))
        .withColumn("_aidp_source_file", F.input_file_name())
        .withColumn("_aidp_batch_id", F.lit(batch_id))
        .withColumn("_aidp_ingested_at", F.current_timestamp())
    )


def write_bronze(name: str, df) -> int:
    table = f"{bronze_catalog}.{bronze_schema}.{name}"
    path = f"{bronze_uri}/{name}"
    (
        add_lineage(df, name)
        .write.mode(config["runtime"]["write_mode"])
        .format("parquet")
        .option("path", path)
        .saveAsTable(table)
    )
    count = spark.table(table).count()
    print(f"{table:<58} {count:>8,} lignes")
    return count

# %% [markdown]
# ## Sources structurees

# %%
counts = {}
for name, filename in CSV_SOURCES.items():
    frame = spark.read.option("header", True).option("escape", '"').csv(f"{raw_uri}/{filename}")
    counts[name] = write_bronze(name, frame)

# %% [markdown]
# ## Sources non structurees

# %%
for name, filename in JSON_SOURCES.items():
    frame = spark.read.json(f"{raw_uri}/{filename}")
    counts[name] = write_bronze(name, frame)

protocols = (
    spark.read.text(f"{raw_uri}/medical_protocols/*.txt", wholetext=True)
    .withColumnRenamed("value", "document_text")
    .withColumn("document_uri", F.input_file_name())
    .withColumn("document_id", F.regexp_extract("document_uri", r"([^/]+)\\.txt$", 1))
)
counts["medical_protocols"] = write_bronze("medical_protocols", protocols)

# %% [markdown]
# ## Controles Bronze

# %%
display(spark.createDataFrame([(name, count) for name, count in counts.items()], ["source", "row_count"]))

for forbidden in ("risk_score", "risk_level", "recommendation", "decision"):
    offending = [name for name in counts if forbidden in spark.table(f"{bronze_catalog}.{bronze_schema}.{name}").columns]
    assert not offending, f"Champ interdit dans les sources Bronze: {forbidden} -> {offending}"

print("Controle reussi: aucune decision ou recommandation n'est presente dans les sources.")
