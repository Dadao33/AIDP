# %% [markdown]
# # Athlete Readiness - 04 Gold et AI Lakehouse
#
# Scoring courant, preuves explicables et publication vers la connexion `SPORT_AGENT`.

# %%
from pathlib import Path
import json

import pandas as pd
from pyspark.sql import functions as F, types as T

# %%
CONFIG_PATH = Path("/Workspace/Config/athlete_readiness_config.json")
if not CONFIG_PATH.exists():
    CONFIG_PATH = Path("../config/athlete_readiness_config.json")
config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

scat, ssch = config["catalog"]["silver_catalog"], config["catalog"]["silver_schema"]
gcat, gsch = config["catalog"]["gold_catalog"], config["catalog"]["gold_schema"]
gold_uri = config["object_storage"]["gold_uri"].rstrip("/")
as_of = config["demo"]["as_of_date"]
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {gcat}.{gsch}")

assert "ATHLETE_READINESS_MODEL" in globals(), "Executer d'abord le notebook 03_ml_training_mlops"

# %%
features = spark.table(f"{scat}.{ssch}.athlete_features_daily")
today = features.where(F.col("observation_date") == F.lit(as_of).cast("date"))
today_pdf = today.select("athlete_id", *ATHLETE_READINESS_FEATURES).toPandas()
today_pdf["injury_risk_7d"] = ATHLETE_READINESS_MODEL.predict_proba(today_pdf[ATHLETE_READINESS_FEATURES])[:, 1]

scores = spark.createDataFrame(today_pdf[["athlete_id", "injury_risk_7d"]])

scored = (
    today.join(scores, "athlete_id", "left")
    .withColumn("risk_rank", F.dense_rank().over(__import__("pyspark").sql.Window.orderBy(F.desc("injury_risk_7d"))))
    .withColumn(
        "risk_band",
        F.when(F.col("injury_risk_7d") >= F.lit(ATHLETE_READINESS_THRESHOLD), "ATTENTION")
        .when(F.col("injury_risk_7d") >= F.lit(ATHLETE_READINESS_THRESHOLD * 0.60), "A_SURVEILLER")
        .otherwise("STABLE"),
    )
    .withColumn("model_run_id", F.lit(ATHLETE_READINESS_RUN_ID))
    .withColumn("scored_at", F.current_timestamp())
)

# 90 jours de scores du même champion alimentent le comparateur du cockpit.
recent_features = features.where(
    (F.col("observation_date") >= F.date_sub(F.lit(as_of).cast("date"), 89))
    & (F.col("observation_date") <= F.lit(as_of).cast("date"))
)
history_pdf = recent_features.select("athlete_id", "observation_date", *ATHLETE_READINESS_FEATURES).toPandas()
history_pdf["injury_risk_7d"] = ATHLETE_READINESS_MODEL.predict_proba(
    history_pdf[ATHLETE_READINESS_FEATURES]
)[:, 1]
history_scores = (
    spark.createDataFrame(history_pdf[["athlete_id", "observation_date", "injury_risk_7d"]])
    .withColumn("observation_date", F.to_date("observation_date"))
)
readiness_history = (
    recent_features.join(history_scores, ["athlete_id", "observation_date"], "left")
    .select(
        "athlete_id", "observation_date", F.round("injury_risk_7d", 4).alias("injury_risk_7d"),
        "hrv_delta_pct", "sleep_hours", "acute_chronic_ratio", "soreness_7d_avg",
        "fatigue_declared_1_10", "gps_intensity_pct", "gps_follow_status",
        "distance_per_min", "high_speed_per_min", "player_load_per_min",
        "nutrition_adherence_pct", "nutrition_status", "hydration_plan_pct",
        "carbohydrate_plan_pct", "protein_plan_pct", "recovery_meal_delay_min",
        F.lit(ATHLETE_READINESS_RUN_ID).alias("model_run_id"),
    )
)

# %% [markdown]
# ## Explications factuelles

# %%
explanations = (
    scored
    .withColumn("signal_hrv", F.when(F.col("hrv_delta_pct") <= -0.10, F.lit("HRV sous la reference individuelle")))
    .withColumn("signal_load", F.when(F.col("acute_chronic_ratio") >= 1.25, F.lit("hausse rapide de charge")))
    .withColumn("signal_sleep", F.when(F.col("sleep_delta_hours") <= -1.0, F.lit("sommeil sous la reference")))
    .withColumn("signal_soreness", F.when(F.col("soreness_7d_avg") >= 5.5, F.lit("courbatures elevees")))
    .withColumn("signal_history", F.when(F.col("days_since_last_injury") <= 60, F.lit("blessure recente")))
    .withColumn("signal_gps", F.when(F.col("gps_follow_status") == "DECROCHAGE", F.lit("decrochage GPS par rapport au poste")))
    .withColumn("signal_nutrition", F.when(F.col("nutrition_status") == "A_REVOIR", F.lit("adherence au plan nutritionnel a revoir")))
    .withColumn("evidence", F.array_compact(F.array("signal_hrv", "signal_load", "signal_sleep", "signal_soreness", "signal_history", "signal_gps", "signal_nutrition")))
    .drop("signal_hrv", "signal_load", "signal_sleep", "signal_soreness", "signal_history", "signal_gps", "signal_nutrition")
)

medical = spark.table(f"{scat}.{ssch}.medical_visits")
declarations = spark.table(f"{scat}.{ssch}.athlete_declarations")
injuries = spark.table(f"{scat}.{ssch}.injury_events")
protocols = spark.table(f"{scat}.{ssch}.medical_protocols")

recent_medical = medical.where(F.col("visit_date") >= F.date_sub(F.lit(as_of).cast("date"), 120))
recent_declarations = declarations.where(F.to_date("declared_at") >= F.date_sub(F.lit(as_of).cast("date"), 90))

# Index documentaire unifié. En production, des vues dédiées appliqueront les
# rôles et politiques de masquage avant exposition au cockpit ou à l'agent.
medical_documents = recent_medical.select(
    F.col("visit_id").alias("document_id"), "athlete_id",
    F.col("visit_date").cast("timestamp").alias("document_date"),
    F.lit("MEDICAL_REPORT").alias("document_type"),
    F.concat_ws(" · ", "visit_type", "practitioner_role").alias("title"),
    F.col("report_text").alias("document_text"),
    F.lit("MEDICAL_STAFF").alias("access_scope"),
)
declaration_documents = recent_declarations.select(
    F.col("declaration_id").alias("document_id"), "athlete_id",
    F.col("declared_at").alias("document_date"),
    F.lit("ATHLETE_DECLARATION").alias("document_type"),
    F.concat(F.lit("Déclaratif · "), F.col("channel")).alias("title"),
    F.col("free_text").alias("document_text"),
    F.lit("PERFORMANCE_AND_MEDICAL").alias("access_scope"),
)
injury_documents = injuries.select(
    F.col("injury_id").alias("document_id"), "athlete_id",
    F.col("injury_date").cast("timestamp").alias("document_date"),
    F.lit("INJURY_HISTORY").alias("document_type"),
    F.concat_ws(" · ", "injury_code", "body_area").alias("title"),
    F.concat(
        F.lit("Épisode "), "episode_type", F.lit(" · "),
        F.col("days_unavailable").cast("string"), F.lit(" jour(s) d'indisponibilité."),
    ).alias("document_text"),
    F.lit("MEDICAL_STAFF").alias("access_scope"),
)
athlete_document_access = (
    medical_documents.unionByName(declaration_documents).unionByName(injury_documents)
)

agent_cases = (
    explanations.where(
        (F.col("risk_rank") <= config["ml"]["top_queue_size"])
        | (F.col("gps_follow_status") != "DANS_LE_RYTHME")
        | (F.col("nutrition_status") == "A_REVOIR")
    )
    .select(
        "athlete_id", "first_name", "last_name", "position", "observation_date", "risk_rank",
        F.round("injury_risk_7d", 4).alias("injury_risk_7d"), "risk_band", "evidence",
        "hrv_delta_pct", "resting_hr_delta", "sleep_delta_hours", "acute_chronic_ratio",
        "high_speed_7d", "soreness_7d_avg", "fatigue_declared_1_10", "days_since_last_injury",
        "session_type", "duration_min", "total_distance_m", "high_speed_distance_m", "sprint_count",
        "player_load_au", "distance_per_min", "high_speed_per_min", "player_load_per_min",
        "distance_vs_position", "high_speed_vs_position", "player_load_vs_position",
        "gps_intensity_pct", "gps_follow_status",
        "hydration_plan_pct", "carbohydrate_plan_pct", "protein_plan_pct",
        "recovery_meal_delay_min", "body_mass_change_pct", "nutrition_self_report_1_10",
        "nutrition_adherence_pct", "nutrition_status",
        "model_run_id", "scored_at",
    )
)

agent_context = (
    agent_cases.alias("c")
    .join(recent_medical.alias("m"), "athlete_id", "left")
    .join(recent_declarations.alias("d"), "athlete_id", "left")
    .groupBy(*[F.col(f"c.{column}") for column in agent_cases.columns])
    .agg(
        F.sort_array(F.collect_set(F.struct("m.visit_date", "m.visit_type", "m.report_text")), asc=False).alias("recent_medical_notes"),
        F.sort_array(F.collect_set(F.struct("d.declared_at", "d.free_text")), asc=False).alias("recent_declarations"),
    )
)

team_summary = explanations.groupBy("risk_band").agg(
    F.countDistinct("athlete_id").alias("athlete_count"),
    F.round(F.avg("injury_risk_7d"), 4).alias("avg_risk"),
    F.round(F.avg("acute_chronic_ratio"), 3).alias("avg_load_ratio"),
)

gps_follow_summary = explanations.groupBy("position", "gps_follow_status").agg(
    F.countDistinct("athlete_id").alias("athlete_count"),
    F.round(F.avg("gps_intensity_pct"), 1).alias("avg_gps_intensity_pct"),
    F.round(F.avg("distance_per_min"), 2).alias("avg_distance_per_min"),
    F.round(F.avg("high_speed_per_min"), 2).alias("avg_high_speed_per_min"),
    F.round(F.avg("player_load_per_min"), 3).alias("avg_player_load_per_min"),
)

nutrition_summary = explanations.where(F.col("nutrition_status") != "NO_DATA").groupBy("nutrition_status").agg(
    F.countDistinct("athlete_id").alias("athlete_count"),
    F.round(F.avg("nutrition_adherence_pct"), 1).alias("avg_nutrition_adherence_pct"),
    F.round(F.avg("hydration_plan_pct"), 1).alias("avg_hydration_plan_pct"),
    F.round(F.avg("carbohydrate_plan_pct"), 1).alias("avg_carbohydrate_plan_pct"),
    F.round(F.avg("protein_plan_pct"), 1).alias("avg_protein_plan_pct"),
)

model_performance = spark.table(f"{scat}.{ssch}.ml_model_performance")
decision_log = spark.createDataFrame([], T.StructType([
    T.StructField("decision_id", T.StringType()), T.StructField("athlete_id", T.StringType()),
    T.StructField("agent_recommendation", T.StringType()), T.StructField("human_status", T.StringType()),
    T.StructField("human_comment", T.StringType()), T.StructField("decided_at", T.TimestampType()),
]))

# %%
gold_objects = {
    "ATHLETE_READINESS_SCORES": explanations,
    "ATHLETE_READINESS_HISTORY": readiness_history,
    "ATHLETE_AGENT_CASES": agent_cases,
    "ATHLETE_AGENT_CONTEXT": agent_context,
    "ATHLETE_DOCUMENT_ACCESS": athlete_document_access,
    "TEAM_READINESS_SUMMARY": team_summary,
    "TEAM_GPS_FOLLOW_SUMMARY": gps_follow_summary,
    "TEAM_NUTRITION_SUMMARY": nutrition_summary,
    "MODEL_PERFORMANCE": model_performance,
    "MEDICAL_PROTOCOL_DOCUMENTS": protocols,
    "AGENT_DECISION_LOG": decision_log,
}

for table_name, frame in gold_objects.items():
    local_table = f"{gcat}.{gsch}.{table_name.lower()}"
    frame.write.mode("overwrite").format("parquet").option("path", f"{gold_uri}/{table_name.lower()}").saveAsTable(local_table)
    print(f"Gold AIDP: {local_table} -> {frame.count():,} lignes")

# %% [markdown]
# ## Publication AI Lakehouse via la connexion AIDP SPORT_AGENT
#
# Le nom de connexion et le schema sont separes afin de ne placer aucun secret dans le notebook.

# %%
target_catalog = config["ai_lakehouse"]["catalog_id"]
target_schema = config["ai_lakehouse"]["schema"]

for table_name, frame in gold_objects.items():
    target = f"{target_catalog}.{target_schema}.{table_name}"
    frame.write.mode("overwrite").saveAsTable(target)
    print(f"AI Lakehouse: {target} -> {spark.table(target).count():,} lignes")

display(agent_context.orderBy("risk_rank"))
