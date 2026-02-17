# Nani
from dagster import asset, Definitions

from src.data_generation import generate_and_store_tickets
from src.train_model import train_models
from src.inference_service import batch_classify_from_db
from src.monitoring import compute_monitoring


# ----------------------------
# INGESTION (Synthetic data -> DB)
# ----------------------------
@asset(group_name="ingestion", compute_kind="python")
def synthetic_data_to_postgres() -> str:
    # Generates + inserts into public.tickets
    generate_and_store_tickets(n_samples=400, seed=7)
    return "Inserted synthetic tickets into PostgreSQL (public.tickets)."


# ----------------------------
# TRAINING (TF-IDF + Logistic Regression)
# ----------------------------
@asset(group_name="training", compute_kind="sklearn", deps=[synthetic_data_to_postgres])
def train_baseline_models() -> dict:
    cat_acc, pri_acc = train_models(test_size=0.2, seed=42)
    return {"category_accuracy": cat_acc, "priority_accuracy": pri_acc}


# ----------------------------
# INFERENCE (Batch classify -> predictions/events)
# ----------------------------
@asset(group_name="inference", compute_kind="sklearn", deps=[train_baseline_models])
def batch_inference_run() -> str:
    # Creates predictions in DB + outputs/predictions.csv + outputs/events.log
    path = batch_classify_from_db(limit=200, seed=2)
    return path


# ----------------------------
# MONITORING (metrics + drift)
# ----------------------------
@asset(group_name="monitoring", compute_kind="sklearn", deps=[batch_inference_run])
def monitoring_report() -> dict:
    # Reads DB (tickets + predictions), writes outputs/metrics.json and CSVs
    metrics = compute_monitoring()
    return metrics


defs = Definitions(
    assets=[
        synthetic_data_to_postgres,
        train_baseline_models,
        batch_inference_run,
        monitoring_report,
    ]
)