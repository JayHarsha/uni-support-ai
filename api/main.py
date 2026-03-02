import time
import threading
import queue
import uuid
import os
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from src.db import (
    insert_incoming_ticket, 
    fetch_tickets_by_student, 
    update_ticket_status
)
from src.inference_service import classify_ticket

app = FastAPI(
    title="University Support AI (Lab 05)",
    version="2.1"
)

# ---------------------------------------------------------
# 1. GLOBAL CONFIG & STATE
# ---------------------------------------------------------
# The Queue stores tuples: (priority_int, ticket_id, text)
# PriorityQueue sorts by the first item (Integer). Smallest = First.
JOB_QUEUE = queue.PriorityQueue()

# Map string inputs to integers for the queue (High=1, Medium=2, Low=3)
PRIORITY_INT_MAP = {"High": 1, "Medium": 2, "Low": 3}

# Lab Metrics
METRICS = {
    "count": 0,
    "total_latency": 0.0
}

# Monolithic Toggle (Environment Variable)
IS_MONOLITHIC = os.getenv("MONOLITHIC_MODE", "false").lower() == "true"


# ---------------------------------------------------------
# 2. WORKER LOOP (The "Cloud" Backend)
# ---------------------------------------------------------
def worker_loop():
    print(f"[Worker] Online. Monolithic Mode: {IS_MONOLITHIC}")
    
    while True:
        try:
            # Get the highest priority item (blocks if empty)
            priority_int, ticket_id, text = JOB_QUEUE.get(timeout=1)
            
            # 1. Update DB -> Processing
            update_ticket_status(ticket_id, "PROCESSING")
            
            # 2. Simulate Heavy Work (Lab Requirement)
            time.sleep(1.0) 
            
            # 3. Run your Project's AI (Business Logic)
            try:
                # We run the AI to categorize the ticket and store prediction
                result = classify_ticket(ticket_id=ticket_id, text=text)
                note = f"AI Classified: {result.get('pred_category')}"
            except Exception as e:
                note = f"AI Error: {str(e)}"

            # 4. Mark Done in Tickets table
            update_ticket_status(ticket_id, "RESOLVED", datetime.now(timezone.utc), note)
            
            JOB_QUEUE.task_done()
            print(f"[Worker] Processed Ticket {ticket_id} (Priority Level: {priority_int})")
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[Worker] Error: {e}")

# Start Worker (Only if NOT Monolithic)
if not IS_MONOLITHIC:
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()


# ---------------------------------------------------------
# 3. MODELS
# ---------------------------------------------------------

# Model for the Lab 05 Submit endpoint
class LabTicketRequest(BaseModel):
    student_id: str
    text: str
    priority: str # User INPUTS "High", "Medium", or "Low"

class TicketResponse(BaseModel):
    ticket_id: str
    status: str
    message: str

# Model for the Original Project Predict endpoint
class TicketRequest(BaseModel):
    text: str

class PredictionResponse(BaseModel):
    ticket_id: str
    category: str
    priority: str
    confidence: float
    processed_at: str


# ---------------------------------------------------------
# 4. ENDPOINTS
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "Online", 
        "mode": "MONOLITHIC" if IS_MONOLITHIC else "ASYNC_QUEUE"
    }

# --- ENDPOINT 1: SUBMIT (Lab Task 1: Priority + Queue) ---
@app.post("/submit", response_model=TicketResponse)
def submit_ticket(req: LabTicketRequest):
    """
    Lab 05 Submit Endpoint.
    - Accepts 'priority' from user.
    - If Async: Pushes to Queue (Fast).
    - If Monolithic: Sleeps/Blocks (Slow).
    """
    start_time = time.time()
    ticket_id = str(uuid.uuid4())[:8]
    created_at = datetime.now(timezone.utc)
    
    # Insert into DB immediately with status="QUEUED"
    insert_incoming_ticket(ticket_id, req.text, created_at, req.student_id, req.priority)
    
    # Convert "High" string to Integer 1
    p_int = PRIORITY_INT_MAP.get(req.priority, 3) 

    if IS_MONOLITHIC:
        # --- MONOLITHIC MODE (The "Bad" Way) ---
        # We simulate processing RIGHT HERE. User waits 1 second.
        time.sleep(1.0)
        
        # Run AI logic immediately
        classify_ticket(ticket_id, req.text)
        update_ticket_status(ticket_id, "RESOLVED", datetime.now(timezone.utc), "Processed Sync")
        
        status = "RESOLVED"
        msg = "Processed Synchronously (Slow)"
    else:
        # --- CLOUD QUEUE MODE (The "Good" Way) ---
        # We push to queue and return IMMEDIATELY.
        JOB_QUEUE.put((p_int, ticket_id, req.text))
        
        status = "QUEUED"
        msg = "Added to Priority Queue"

    # Update Metrics
    duration = time.time() - start_time
    METRICS["count"] += 1
    METRICS["total_latency"] += duration

    return TicketResponse(ticket_id=ticket_id, status=status, message=msg)


# --- ENDPOINT 2: GET BY STUDENT (Lab Task 2) ---
@app.get("/tickets")
def get_tickets_by_student(student_id: str = Query(..., description="The Student ID to search for")):
    """
    Returns all tickets for a specific student_id.
    Example: GET /tickets?student_id=S12345
    """
    tickets = fetch_tickets_by_student(student_id)
    return {"student_id": student_id, "tickets": tickets}


# --- ENDPOINT 3: METRICS (Lab Task 3) ---
@app.get("/metrics")
def get_metrics():
    avg = 0
    if METRICS["count"] > 0:
        avg = METRICS["total_latency"] / METRICS["count"]
    
    return {
        "total_requests": METRICS["count"],
        "average_response_time_seconds": round(avg, 4),
        "current_queue_length": JOB_QUEUE.qsize(),
        "mode": "MONOLITHIC" if IS_MONOLITHIC else "ASYNC_QUEUE"
    }


# --- ENDPOINT 4: ORIGINAL PROJECT PREDICT ---
@app.post("/predict", response_model=PredictionResponse)
def predict_original(req: TicketRequest):
    """
    Original synchronous AI endpoint.
    Doesn't use the queue. Uses default 'Anonymous' student_id.
    """
    ticket_id = str(uuid.uuid4())[:8]
    
    # Uses the default student_id="Anonymous"
    insert_incoming_ticket(ticket_id, req.text, datetime.now(timezone.utc))
    
    # Run AI immediately
    result = classify_ticket(ticket_id, req.text)
    
    return PredictionResponse(
        ticket_id=ticket_id,
        category=result.get("pred_category", "Unknown"),
        priority=result.get("pred_priority", "Unknown"),
        confidence=result.get("confidence", 0.0),
        processed_at=datetime.now(timezone.utc).isoformat()
    )