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
    """
    Used by Data Generation script (Synthetic data).
    """
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


def insert_incoming_ticket(ticket_id, text, created_at, student_id="Anonymous", priority="Low"):
    """
    Used by API /submit endpoint.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO public.tickets
            (ticket_id, student_id, text, true_category, true_priority, requested_priority, status, created_at)
            VALUES (%s, %s, %s, 'Unknown', 'Unknown', %s, 'QUEUED', %s)
            ON CONFLICT (ticket_id) DO NOTHING;
            """,
            (ticket_id, student_id, text, priority, created_at),
        )


def fetch_all_tickets():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM public.tickets;")
        return cur.fetchall()


def fetch_tickets_by_student(student_id):
    """
    Lab Req: Get history for a specific student.
    """
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM public.tickets WHERE student_id = %s ORDER BY created_at DESC;",
            (student_id,)
        )
        return cur.fetchall()


def update_ticket_status(ticket_id, status, resolved_at=None, note=None):
    """
    Used by Worker to update status (PROCESSING -> RESOLVED).
    """
    with get_cursor() as cur:
        if resolved_at:
            cur.execute(
                """
                UPDATE public.tickets 
                SET status = %s, resolved_at = %s, resolution_note = %s 
                WHERE ticket_id = %s;
                """,
                (status, resolved_at, note, ticket_id)
            )
        else:
            cur.execute(
                "UPDATE public.tickets SET status = %s WHERE ticket_id = %s;",
                (status, ticket_id)
            )


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

# --------------------------------------------------
# High Urgency Tickets
# --------------------------------------------------
def fetch_unclassified_tickets(limit=200):
    """
    Fetch tickets not yet classified.
    """
    limit = int(limit)
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT t.*
            FROM public.tickets t
            LEFT JOIN public.predictions p
                ON t.ticket_id = p.ticket_id
            WHERE p.ticket_id IS NULL
            ORDER BY t.created_at DESC
            LIMIT {limit};
            """
        )
        return cur.fetchall()