# src/monitoring.py

import json
import os
from typing import Dict, Any

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)

from src.config import (
    OUTPUT_DIR,
    METRICS_JSON_PATH,
    CONFUSION_MATRIX_CSV_PATH,
    HIGH_PRIORITY_PER_DAY_CSV_PATH,
    DRIFT_CSV_PATH,
)
from src.db import fetch_all_tickets, fetch_all_predictions, insert_metrics


def _load_joined_data() -> pd.DataFrame:
    """
    Join tickets (true labels + created_at) with predictions (model outputs).
    We join on ticket_id so we can compare true vs predicted.
    """
    tickets = pd.DataFrame(fetch_all_tickets())
    preds = pd.DataFrame(fetch_all_predictions())

    if tickets.empty:
        raise RuntimeError("No tickets found. Run src.data_generation first.")
    if preds.empty:
        raise RuntimeError("No predictions found. Run src.inference_service first.")

    df = preds.merge(
        tickets[["ticket_id", "true_category", "true_priority", "created_at"]],
        on="ticket_id",
        how="left"
    )

    # Clean and parse timestamps
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df["processed_at"] = pd.to_datetime(df["processed_at"], utc=True, errors="coerce")
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")

    # Minimal hygiene
    df = df.dropna(subset=["true_category", "pred_category", "created_at", "confidence"])
    return df


def compute_monitoring() -> Dict[str, Any]:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = _load_joined_data()

    # -----------------------------
    # 1) Core classification metrics (Category)
    # -----------------------------
    y_true = df["true_category"].astype(str)
    y_pred = df["pred_category"].astype(str)

    acc = float(accuracy_score(y_true, y_pred))

    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )

    # Useful report for write-up (per class)
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    # Confusion matrix
    labels = sorted(list(set(y_true) | set(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=[f"true_{l}" for l in labels], columns=[f"pred_{l}" for l in labels])
    cm_df.to_csv(CONFUSION_MATRIX_CSV_PATH, index=True)

    # -----------------------------
    # 2) High-priority tickets per day (Predicted)
    # -----------------------------
    df["day"] = df["created_at"].dt.date.astype(str)
    high_per_day = (
        df[df["pred_priority"].astype(str) == "High"]
        .groupby("day")["ticket_id"]
        .count()
        .reset_index()
        .rename(columns={"ticket_id": "high_priority_count"})
        .sort_values("day")
    )
    high_per_day.to_csv(HIGH_PRIORITY_PER_DAY_CSV_PATH, index=False)

    # -----------------------------
    # 3) Drift check (simple): avg confidence over time (per day)
    # -----------------------------
    drift = (
        df.groupby("day")["confidence"]
        .mean()
        .reset_index()
        .rename(columns={"confidence": "avg_confidence"})
        .sort_values("day")
    )
    drift.to_csv(DRIFT_CSV_PATH, index=False)

    avg_conf_overall = float(df["confidence"].mean())

    # -----------------------------
    # 4) Store summary metrics in DB
    # -----------------------------
    insert_metrics(
        category_accuracy=acc,
        precision_macro=float(precision_macro),
        recall_macro=float(recall_macro),
        f1_macro=float(f1_macro),
        avg_confidence=avg_conf_overall
    )

    # -----------------------------
    # 5) Write metrics.json for submission
    # -----------------------------
    metrics_out = {
        "n_predictions": int(len(df)),
        "category_accuracy": acc,
        "precision_macro": float(precision_macro),
        "recall_macro": float(recall_macro),
        "f1_macro": float(f1_macro),
        "avg_confidence": avg_conf_overall,
        "labels": labels,
        "category_classification_report": report,
        "artifacts": {
            "metrics_json": METRICS_JSON_PATH,
            "confusion_matrix_csv": CONFUSION_MATRIX_CSV_PATH,
            "high_priority_per_day_csv": HIGH_PRIORITY_PER_DAY_CSV_PATH,
            "drift_csv": DRIFT_CSV_PATH,
        }
    }

    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_out, f, indent=2)

    print(f"[OK] Metrics written -> {METRICS_JSON_PATH}")
    print(f"[OK] Confusion matrix -> {CONFUSION_MATRIX_CSV_PATH}")
    print(f"[OK] High priority per day -> {HIGH_PRIORITY_PER_DAY_CSV_PATH}")
    print(f"[OK] Drift confidence -> {DRIFT_CSV_PATH}")
    print(f"[Summary] Category Accuracy={acc:.4f}, F1(macro)={f1_macro:.4f}, AvgConf={avg_conf_overall:.4f}")

    return metrics_out


if __name__ == "__main__":
    compute_monitoring()
