import os

# -------------------------
# Database (PostgreSQL)
# -------------------------
# You provided JDBC:
# jdbc:postgresql://localhost:5432/uni_support_ai
# Python (psycopg2) format:
# postgresql://USER:PASSWORD@HOST:PORT/DB
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))
DB_NAME = os.getenv("DB_NAME", "uni_support_ai")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "@Qwerty7")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

# -------------------------
# Outputs (artifacts)
# -------------------------
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")

VECTORIZER_PATH = os.path.join(OUTPUT_DIR, "vectorizer.joblib")
CATEGORY_MODEL_PATH = os.path.join(OUTPUT_DIR, "category_model.joblib")
PRIORITY_MODEL_PATH = os.path.join(OUTPUT_DIR, "priority_model.joblib")

METRICS_JSON_PATH = os.path.join(OUTPUT_DIR, "metrics.json")
CONFUSION_MATRIX_CSV_PATH = os.path.join(OUTPUT_DIR, "confusion_matrix.csv")
HIGH_PRIORITY_PER_DAY_CSV_PATH = os.path.join(OUTPUT_DIR, "high_priority_per_day.csv")
DRIFT_CSV_PATH = os.path.join(OUTPUT_DIR, "drift_confidence_over_time.csv")

# -------------------------
# Model / inference settings
# -------------------------
# If confidence is below this, we can flag it (optional improvement)
LOW_CONFIDENCE_THRESHOLD = float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.60"))

# Categories required by assignment
CATEGORIES = ["IT", "Fees", "Timetable", "Exams", "General"]
PRIORITIES = ["Low", "Medium", "High"]
