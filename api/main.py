# Watashi

from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from src.db import insert_incoming_ticket
from src.inference_service import classify_ticket

app = FastAPI(
    title="University Support AI",
    description="AI-based ticket classification system",
    version="1.0"
)


class TicketRequest(BaseModel):
    text: str


class PredictionResponse(BaseModel):
    ticket_id: str
    category: str
    priority: str
    confidence: float
    processed_at: str


@app.get("/")
def root():
    return {"message": "University Support AI is running"}


@app.post("/predict", response_model=PredictionResponse)
def predict_ticket(request: TicketRequest):
    """
    Classify a new incoming support ticket.
    """

    ticket_id = str(uuid.uuid4())[:8]
    insert_incoming_ticket(ticket_id, request.text, datetime.now(timezone.utc))
    result = classify_ticket(ticket_id=ticket_id, text=request.text)

    return PredictionResponse(
        ticket_id=ticket_id,
        category=result["category"],
        priority=result["priority"],
        confidence=result["confidence"],
        processed_at=result["processed_at"]
    )
