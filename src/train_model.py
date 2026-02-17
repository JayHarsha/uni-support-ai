# Nani
import os
import pandas as pd
from typing import Tuple

from joblib import dump
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from src.config import (
    OUTPUT_DIR,
    CATEGORY_MODEL_PATH,
    PRIORITY_MODEL_PATH
)
from src.db import fetch_all_tickets


def _load_training_data() -> pd.DataFrame:
    rows = fetch_all_tickets()
    if not rows:
        raise RuntimeError("No tickets found in DB. Run data_generation first.")

    df = pd.DataFrame(rows)
    df["text"] = df["text"].astype(str).str.strip()
    df = df.dropna(subset=["text", "true_category", "true_priority"])
    return df


def train_models(test_size: float = 0.2, seed: int = 42) -> Tuple[float, float]:

    df = _load_training_data()

    X = df["text"]
    y_cat = df["true_category"]
    y_pri = df["true_priority"]

    X_train, X_test, y_cat_train, y_cat_test, y_pri_train, y_pri_test = train_test_split(
        X,
        y_cat,
        y_pri,
        test_size=test_size,
        random_state=seed,
        stratify=y_cat
    )

    # -----------------------------
    # Category Classification Pipeline
    # -----------------------------
    category_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_features=5000
        )),
        ("clf", LogisticRegression(max_iter=300))
    ])

    # -----------------------------
    # Priority Classification Pipeline
    # -----------------------------
    priority_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_features=5000
        )),
        ("clf", LogisticRegression(max_iter=300))
    ])

    # Train models
    category_pipeline.fit(X_train, y_cat_train)
    priority_pipeline.fit(X_train, y_pri_train)

    # Evaluate
    cat_pred = category_pipeline.predict(X_test)
    pri_pred = priority_pipeline.predict(X_test)

    cat_acc = accuracy_score(y_cat_test, cat_pred)
    pri_acc = accuracy_score(y_pri_test, pri_pred)

    # Save models
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dump(category_pipeline, CATEGORY_MODEL_PATH)
    dump(priority_pipeline, PRIORITY_MODEL_PATH)

    print(f"[OK] Saved category model -> {CATEGORY_MODEL_PATH}")
    print(f"[OK] Saved priority model -> {PRIORITY_MODEL_PATH}")
    print(f"[Baseline] Category accuracy: {cat_acc:.4f}")
    print(f"[Baseline] Priority accuracy: {pri_acc:.4f}")

    return cat_acc, pri_acc


if __name__ == "__main__":
    train_models()