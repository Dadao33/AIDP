# %% [markdown]
# # Athlete Readiness - 02 Silver
#
# Typage, controles qualite, fenetres temporelles et reconstruction du label historique.

# %%
from pathlib import Path
import json

from pyspark.sql import Window, functions as F, types as T

# %%
CONFIG_PATH = Path("/Workspace/Config/athlete_readiness_config.json")
if not CONFIG_PATH.exists():
    CONFIG_PATH = Path("../config/athlete_readiness_config.json")
config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

bcat, bsch = config["catalog"]["bronze_catalog"], config["catalog"]["bronze_schema"]
scat, ssch = config["catalog"]["silver_catalog"], config["catalog"]["silver_schema"]
silver_uri = config["object_storage"]["silver_uri"].rstrip("/")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {scat}.{ssch}")


def bronze(name: str):
    return spark.table(f"{bcat}.{bsch}.{name}")


def publish(name: str, frame) -> int:
    table = f"{scat}.{ssch}.{name}"
    path = f"{silver_uri}/{name}"
    frame.write.mode("overwrite").format("parquet").option("path", path).saveAsTable(table)
    count = spark.table(table).count()
    print(f"{table:<60} {count:>8,} lignes")
    return count

# %%
athletes = (
    bronze("athletes")
    .select(
        "athlete_id", "first_name", "last_name", "position", F.to_date("birth_date").alias("birth_date"),
        F.col("height_cm").cast("int"), F.col("weight_kg").cast("int"), "dominant_leg",
        F.col("baseline_hrv_ms").cast("double"), F.col("baseline_resting_hr_bpm").cast("double"),
        F.col("baseline_sleep_hours").cast("double"), "squad",
    )
    .dropDuplicates(["athlete_id"])
)

wellness = bronze("daily_wellness").select(
    F.to_date("observation_date").alias("observation_date"), "athlete_id",
    *[F.col(c).cast("double").alias(c) for c in [
        "sleep_hours", "sleep_quality_1_10", "soreness_1_10", "stress_1_10",
        "mood_1_10", "fatigue_declared_1_10",
    ]],
)

training = bronze("training_load").select(
    F.to_date("session_date").alias("observation_date"), "athlete_id", "session_type",
    *[F.col(c).cast("double").alias(c) for c in [
        "duration_min", "total_distance_m", "high_speed_distance_m", "sprint_count",
        "accelerations_count", "session_rpe_1_10", "player_load_au", "minutes_played",
    ]],
)

nutrition = bronze("nutrition_tracking").select(
    F.to_date("observation_date").alias("observation_date"), "athlete_id",
    *[F.col(c).cast("double").alias(c) for c in [
        "hydration_plan_pct", "carbohydrate_plan_pct", "protein_plan_pct",
        "recovery_meal_delay_min", "body_mass_change_pct", "nutrition_self_report_1_10",
    ]],
    "source_system",
)

wearable = bronze("wearable_recovery").select(
    F.to_date("observation_date").alias("observation_date"), "athlete_id",
    *[F.col(c).cast("double").alias(c) for c in [
        "hrv_rmssd_ms", "resting_hr_bpm", "respiratory_rate",
        "skin_temperature_delta_c", "wear_time_hours", "device_quality_pct",
    ]],
)

calendar = bronze("competition_calendar").select(
    F.to_date("event_date").alias("observation_date"), "event_type", "venue",
    F.col("travel_hours").cast("double"), "surface", F.col("temperature_c").cast("double"),
)

injuries = bronze("injury_events").select(
    "injury_id", "athlete_id", F.to_date("event_date").alias("injury_date"),
    "injury_code", "body_area", "mechanism", F.col("days_unavailable").cast("int"), "episode_type",
)

# %% [markdown]
# ## Feature engineering sans fuite de cible

# %%
daily = wellness.join(training, ["athlete_id", "observation_date"], "inner") \
    .join(wearable, ["athlete_id", "observation_date"], "inner") \
    .join(nutrition, ["athlete_id", "observation_date"], "left") \
    .join(calendar, "observation_date", "left") \
    .join(athletes, "athlete_id", "left")

by_athlete = Window.partitionBy("athlete_id").orderBy(F.col("observation_date").cast("timestamp").cast("long"))
w7 = by_athlete.rowsBetween(-6, 0)
w28_prev = by_athlete.rowsBetween(-28, -1)
by_position_session = Window.partitionBy("observation_date", "session_type", "position")

features = (
    daily
    # Intensite GPS comparable entre joueurs, quelle que soit la duree de la seance.
    .withColumn("distance_per_min", F.round(F.col("total_distance_m") / F.greatest(F.col("duration_min"), F.lit(1.0)), 3))
    .withColumn("high_speed_per_min", F.round(F.col("high_speed_distance_m") / F.greatest(F.col("duration_min"), F.lit(1.0)), 3))
    .withColumn("player_load_per_min", F.round(F.col("player_load_au") / F.greatest(F.col("duration_min"), F.lit(1.0)), 3))
    .withColumn("position_distance_per_min_ref", F.percentile_approx("distance_per_min", 0.5).over(by_position_session))
    .withColumn("position_high_speed_per_min_ref", F.percentile_approx("high_speed_per_min", 0.5).over(by_position_session))
    .withColumn("position_player_load_per_min_ref", F.percentile_approx("player_load_per_min", 0.5).over(by_position_session))
    .withColumn("distance_vs_position", F.round(F.col("distance_per_min") / F.greatest(F.col("position_distance_per_min_ref"), F.lit(0.01)), 3))
    .withColumn("high_speed_vs_position", F.round(F.col("high_speed_per_min") / F.greatest(F.col("position_high_speed_per_min_ref"), F.lit(0.01)), 3))
    .withColumn("player_load_vs_position", F.round(F.col("player_load_per_min") / F.greatest(F.col("position_player_load_per_min_ref"), F.lit(0.01)), 3))
    .withColumn(
        "gps_intensity_pct",
        F.round(
            F.lit(100.0) * (
                F.lit(0.40) * F.least(F.col("distance_vs_position"), F.lit(1.20))
                + F.lit(0.30) * F.least(F.col("high_speed_vs_position"), F.lit(1.20))
                + F.lit(0.30) * F.least(F.col("player_load_vs_position"), F.lit(1.20))
            ),
            1,
        ),
    )
    .withColumn(
        "gps_follow_status",
        F.when(
            (F.col("distance_vs_position") < 0.85)
            & (F.col("high_speed_vs_position") < 0.70)
            & (F.col("player_load_vs_position") < 0.85),
            F.lit("DECROCHAGE"),
        )
        .when(F.col("gps_intensity_pct") < 90.0, F.lit("SOUS_CIBLE"))
        .otherwise(F.lit("DANS_LE_RYTHME")),
    )
    .withColumn(
        "nutrition_adherence_pct",
        F.when(F.col("hydration_plan_pct").isNull(), F.lit(None).cast("double")).otherwise(
            F.round(
                F.lit(0.30) * F.least(F.col("hydration_plan_pct"), F.lit(100.0))
                + F.lit(0.30) * F.least(F.col("carbohydrate_plan_pct"), F.lit(100.0))
                + F.lit(0.20) * F.least(F.col("protein_plan_pct"), F.lit(100.0))
                + F.lit(0.20) * F.greatest(F.lit(0.0), F.lit(100.0) - F.greatest(F.col("recovery_meal_delay_min") - F.lit(30.0), F.lit(0.0)) * F.lit(0.8)),
                1,
            )
        ),
    )
    .withColumn(
        "nutrition_status",
        F.when(F.col("hydration_plan_pct").isNull(), F.lit("NO_DATA"))
        .when(
            (F.col("hydration_plan_pct") < 80)
            | (F.col("carbohydrate_plan_pct") < 75)
            | (F.col("recovery_meal_delay_min") > 90)
            | (F.col("body_mass_change_pct") <= -1.5),
            F.lit("A_REVOIR"),
        )
        .when(
            (F.col("hydration_plan_pct") < 90)
            | (F.col("carbohydrate_plan_pct") < 90)
            | (F.col("protein_plan_pct") < 90)
            | (F.col("recovery_meal_delay_min") > 60),
            F.lit("A_RENFORCER"),
        )
        .otherwise(F.lit("ALIGNE")),
    )
    .withColumn("acute_load_7d", F.sum("player_load_au").over(w7))
    .withColumn("chronic_load_28d", F.avg("player_load_au").over(w28_prev) * F.lit(7.0))
    .withColumn("acute_chronic_ratio", F.round(F.col("acute_load_7d") / F.greatest(F.col("chronic_load_28d"), F.lit(1.0)), 3))
    .withColumn("high_speed_7d", F.sum("high_speed_distance_m").over(w7))
    .withColumn("sprint_count_7d", F.sum("sprint_count").over(w7))
    .withColumn("sleep_7d_avg", F.avg("sleep_hours").over(w7))
    .withColumn("soreness_7d_avg", F.avg("soreness_1_10").over(w7))
    .withColumn("hrv_delta_pct", F.round((F.col("hrv_rmssd_ms") - F.col("baseline_hrv_ms")) / F.col("baseline_hrv_ms"), 4))
    .withColumn("resting_hr_delta", F.round(F.col("resting_hr_bpm") - F.col("baseline_resting_hr_bpm"), 2))
    .withColumn("sleep_delta_hours", F.round(F.col("sleep_hours") - F.col("baseline_sleep_hours"), 2))
)

# A label is reconstructed from observed injury dates; it never existed in raw data.
future_injuries = injuries.select("athlete_id", "injury_date")
features = (
    features.alias("f")
    .join(
        future_injuries.alias("i"),
        (F.col("f.athlete_id") == F.col("i.athlete_id"))
        & (F.col("i.injury_date") > F.col("f.observation_date"))
        & (F.col("i.injury_date") <= F.date_add(F.col("f.observation_date"), config["ml"]["prediction_horizon_days"])),
        "left",
    )
    .groupBy(*[F.col(f"f.{c}") for c in features.columns])
    .agg(F.max(F.when(F.col("i.injury_date").isNotNull(), 1).otherwise(0)).alias("injury_next_7d"))
)

last_injury = injuries.select("athlete_id", "injury_date", "body_area")
features = (
    features.alias("f")
    .join(last_injury.alias("h"), (F.col("f.athlete_id") == F.col("h.athlete_id")) & (F.col("h.injury_date") < F.col("f.observation_date")), "left")
    .groupBy(*[F.col(f"f.{c}") for c in features.columns])
    .agg(
        F.max("h.injury_date").alias("last_injury_date"),
        F.count("h.injury_date").alias("prior_injury_count"),
    )
    .withColumn("days_since_last_injury", F.coalesce(F.datediff("observation_date", "last_injury_date"), F.lit(9999)))
)

# %% [markdown]
# ## Texte medical et declaratif

# %%
medical_visits = bronze("medical_visits").select(
    "visit_id", "athlete_id", F.to_date("visit_date").alias("visit_date"),
    "practitioner_role", "visit_type", "report_text", "document_format",
)
declarations = bronze("athlete_declarations").select(
    "declaration_id", "athlete_id", F.to_timestamp("declared_at").alias("declared_at"), "channel", "free_text",
)
protocols = bronze("medical_protocols").select("document_id", "document_uri", "document_text")

# %% [markdown]
# ## Qualite et publication Silver

# %%
quality = [
    ("athlete_id_not_null", features.where(F.col("athlete_id").isNull()).count()),
    ("unique_athlete_day", features.count() - features.dropDuplicates(["athlete_id", "observation_date"]).count()),
    ("sleep_in_range", features.where(~F.col("sleep_hours").between(3, 12)).count()),
    ("hrv_positive", features.where(F.col("hrv_rmssd_ms") <= 0).count()),
]
quality_df = spark.createDataFrame(quality, ["rule_name", "failed_rows"]).withColumn("checked_at", F.current_timestamp())
assert quality_df.agg(F.sum("failed_rows")).first()[0] == 0, "Echec des controles qualite Silver"

publish("athlete_features_daily", features)
publish("injury_events", injuries)
publish("medical_visits", medical_visits)
publish("athlete_declarations", declarations)
publish("medical_protocols", protocols)
publish("data_quality_results", quality_df)

display(features.groupBy("injury_next_7d").count().orderBy("injury_next_7d"))
display(features.orderBy(F.desc("observation_date"), F.desc("acute_chronic_ratio")).limit(20))
