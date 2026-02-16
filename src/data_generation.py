# src/data_generation.py

import random
from datetime import datetime, timedelta, timezone
import uuid

from src.config import CATEGORIES
from src.db import insert_ticket


# -------------------------------------------
# Simple text templates for each category
# -------------------------------------------

TEMPLATES = {
    "IT": [
        "I can't access Moodle.",
        "My university login is not working.",
        "WiFi is not connecting on campus.",
        "I forgot my password.",
        "The portal shows an internal server error."
    ],
    "Fees": [
        "My fee payment failed.",
        "I was charged twice for tuition.",
        "The payment portal is not working.",
        "I need a receipt for my payment.",
        "My bank transfer is still pending."
    ],
    "Timetable": [
        "My timetable shows overlapping classes.",
        "I need to change my tutorial group.",
        "My timetable is missing lab sessions.",
        "I cannot see my updated timetable.",
        "Wrong module assigned in timetable."
    ],
    "Exams": [
        "I need an exam deferral.",
        "My exam venue is not displayed.",
        "I missed my exam due to illness.",
        "I need exam accommodation.",
        "Exam timetable seems incorrect."
    ],
    "General": [
        "I need help with enrollment.",
        "Who should I contact for student services?",
        "I submitted a request last week.",
        "I have an issue with my ID card.",
        "Need guidance about attendance rules."
    ],
}


# -------------------------------------------
# Priority rule (simple but logical)
# -------------------------------------------

def assign_priority(category, text):
    text = text.lower()

    if category in ["Exams", "Fees"]:
        return "High"
    if category == "IT" and "can't" in text:
        return "High"
    if category == "Timetable":
        return "Medium"
    return "Low"


# -------------------------------------------
# Generate and insert tickets
# -------------------------------------------

def generate_and_store_tickets(n_samples=300, seed=42):
    random.seed(seed)

    base_time = datetime.now(timezone.utc) - timedelta(days=30)

    for _ in range(n_samples):
        category = random.choice(CATEGORIES)
        text = random.choice(TEMPLATES[category])
        priority = assign_priority(category, text)

        created_at = base_time + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        ticket_id = str(uuid.uuid4())[:8]

        insert_ticket(
            ticket_id=ticket_id,
            text=text,
            true_category=category,
            true_priority=priority,
            created_at=created_at
        )

    print(f"Inserted {n_samples} synthetic tickets into database.")


if __name__ == "__main__":
    generate_and_store_tickets(n_samples=300)
