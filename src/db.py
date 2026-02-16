# src/db.py

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager

from src.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


# --------------------------------------------------
# Database Connection
# --------------------------------------------------

def get_connection():
    """
    Create a new database connection.
    """
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


@contextmanager
def get_cursor():
    """
    Context manager for DB cursor.
    Automatically commits and closes.
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


# --------------------------------------------------
# Tickets
# --------------------------------------------------

def insert_ticket(ticket_id, text, true_category, true_priority, created_at):
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.tickets
            (ticket_id, text, true_category, true_priority, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ticket_id) DO NOTHING;
            """,
            (ticket_id, text, true_category, true_priority, created_at),
        )


def fetch_all_tickets():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM public.tickets;")
        return cur.fetchall()


# --------------------------------------------------
# Predictions
# --------------------------------------------------

def insert_prediction(ticket_id, pred_category, pred_priority, confidence):
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.predictions
            (ticket_id, pred_category, pred_priority, confidence)
            VALUES (%s, %s, %s, %s);
            """,
            (ticket_id, pred_category, pred_priority, confidence),
        )


def fetch_all_predictions():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM public.predictions;")
        return cur.fetchall()


# --------------------------------------------------
# Events
# --------------------------------------------------

def insert_event(event_type, payload):
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.events
            (event_type, payload)
            VALUES (%s, %s);
            """,
            (event_type, Json(payload)),
        )


# --------------------------------------------------
# Metrics
# --------------------------------------------------

def insert_metrics(category_accuracy, precision_macro, recall_macro, f1_macro, avg_confidence):
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.metrics
            (category_accuracy, precision_macro, recall_macro, f1_macro, avg_confidence)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (category_accuracy, precision_macro, recall_macro, f1_macro, avg_confidence),
        )
