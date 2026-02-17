# Vinaya

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
from joblib import load
from src.db import fetch_unclassified_tickets

from src.config import (
    OUTPUT_DIR,
    CATEGORY_MODEL_PATH,
    PRIORITY_MODEL_PATH,
)
from src.db import insert_prediction, insert_event, fetch_all_tickets
from src.event_bus import BUS


EVENTS_LOG_PATH = os.path.join(OUTPUT_DIR, "events.log")
PREDICTIONS_CSV_PATH = os.path.join(OUTPUT_DIR, "predictions.csv")


_category_model = None
_priority_model = None


def _lazy_load_models():
    global _category_model, _priority_model
    if _category_model is None:
        _category_model = load(CATEGORY_MODEL_PATH)
    if _priority_model is None:
        _priority_model = load(PRIORITY_MODEL_PATH)


def predict_text(text: str) -> Dict[str, Any]:
    """
    Predict category + priority for a single ticket text.
    Returns predictions + confidence.
    """
    _lazy_load_models()

    # Category prediction + confidence
    cat_proba = _category_model.predict_proba([text])[0]
    cat_classes = list(_category_model.classes_)
    cat_idx = int(cat_proba.argmax())
    pred_category = cat_classes[cat_idx]
    cat_conf = float(cat_proba[cat_idx])

    # Priority prediction + confidence
    pri_proba = _priority_model.predict_proba([text])[0]
    pri_classes = list(_priority_model.classes_)
    pri_idx = int(pri_proba.argmax())
    pred_priority = pri_classes[pri_idx]
    pri_conf = float(pri_proba[pri_idx])

    # Single confidence score (simple + explainable)
    confidence = float((cat_conf + pri_conf) / 2.0)

    return {
        "pred_category": pred_category,
        "pred_priority": pred_priority,
        "confidence": confidence,
        "category_confidence": cat_conf,
        "priority_confidence": pri_conf,
    }


def classify_ticket(ticket_id: str, text: str) -> Dict[str, Any]:
    """
    Predict, publish an event, and store results in Postgres.
    """
    result = predict_text(text)

    event_payload = {
        "event": "TICKET_CLASSIFIED",
        "ticket_id": ticket_id,
        "category": result["pred_category"],
        "priority": result["pred_priority"],
        "confidence": round(result["confidence"], 6),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    # 1) Publish to in-memory queue (simulation)
    # BUS.publish(event_payload)

    # 2) Store in Postgres for persistence
    insert_prediction(
        ticket_id=ticket_id,
        pred_category=result["pred_category"],
        pred_priority=result["pred_priority"],
        confidence=result["confidence"],
    )

    if result["pred_priority"] == "High":
        BUS.publish(event_payload)
        insert_event(event_type="TICKET_CLASSIFIED", payload=event_payload)

    # insert_event(event_type="TICKET_CLASSIFIED", payload=event_payload)

    return event_payload


def batch_classify_from_db(limit: int = 200, seed: int = 42) -> str:
    """
    Batch inference for pipeline/testing:
    - reads tickets from DB
    - classifies a sample
    - writes outputs/predictions.csv
    - drains event bus and writes outputs/events.log
    """
    # rows = fetch_all_tickets()
    rows = fetch_unclassified_tickets(limit=limit)

    if not rows:
        raise RuntimeError("No tickets found. Run data_generation first.")

    df = pd.DataFrame(rows)

    # Sample (so we don't predict everything every time)
    df = df.sample(n=min(limit, len(df)), random_state=seed).reset_index(drop=True)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    preds_out: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        ticket_id = str(row["ticket_id"])
        text = str(row["text"])

        event = classify_ticket(ticket_id, text)

        preds_out.append(
            {
                "ticket_id": ticket_id,
                "text": text,
                "true_category": row["true_category"],
                "true_priority": row["true_priority"],
                "pred_category": event["category"],
                "pred_priority": event["priority"],
                "confidence": event["confidence"],
                "created_at": str(row["created_at"]),
                "processed_at": event["processed_at"],
            }
        )

    pred_df = pd.DataFrame(preds_out).sort_values("created_at")
    pred_df.to_csv(PREDICTIONS_CSV_PATH, index=False)

    # Drain queue and write event log (so you show consume side)
    drained = BUS.consume(max_events=10_000)
    with open(EVENTS_LOG_PATH, "w", encoding="utf-8") as f:
        for evt in drained:
            f.write(f"{evt}\n")

    print(f"[OK] Wrote predictions -> {PREDICTIONS_CSV_PATH} ({len(pred_df)} rows)")
    print(f"[OK] Wrote events log -> {EVENTS_LOG_PATH} ({len(drained)} events)")
    return PREDICTIONS_CSV_PATH


if __name__ == "__main__":
    # Run a batch inference run (for testing)
    batch_classify_from_db(limit=200, seed=2)