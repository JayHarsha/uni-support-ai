# Watashi

import random
from datetime import datetime, timedelta, timezone
import uuid

from src.config import CATEGORIES
from src.db import insert_ticket


# Shared phrases across multiple categories (creates overlap)
SHARED_PHRASES = [
    "The portal is showing an error.",
    "I need help as soon as possible.",
    "This is urgent due to a deadline.",
    "I tried multiple times but it still fails.",
    "It worked yesterday but not today.",
    "I am getting a timeout message.",
]

# Category-specific templates (still meaningful, but less deterministic)
TEMPLATES = {
    "IT": [
        "I can't access Moodle.",
        "My university login is not working.",
        "Password reset is not working.",
        "I get invalid credentials when logging in.",
        "Moodle page is not loading for my course.",
    ],
    "Fees": [
        "My payment failed on the fee portal.",
        "I was charged twice for tuition.",
        "My transaction was declined.",
        "I need a receipt for my fee payment.",
        "The billing page is not loading when I try to pay.",
    ],
    "Timetable": [
        "My timetable shows overlapping classes.",
        "I need to change my tutorial group.",
        "My timetable is missing lab sessions.",
        "The timetable page is not loading.",
        "Wrong module is assigned in my timetable.",
    ],
    "Exams": [
        "I need an exam deferral.",
        "My exam venue is not displayed.",
        "My exam timetable seems incorrect.",
        "I missed my exam due to illness.",
        "I need exam accommodation support.",
    ],
    "General": [
        "I need help with enrollment.",
        "Who should I contact for student services?",
        "I have an issue with my ID card.",
        "I need guidance about attendance rules.",
        "I submitted a request last week and got no update.",
    ],
}

URGENCY_WORDS = ["urgent", "today", "deadline", "tomorrow", "asap", "immediately"]
DEADLINE_CONTEXT = [
    "My exam is tomorrow.",
    "Enrollment deadline is today.",
    "Fees deadline is tomorrow.",
    "My class starts today.",
]


def assign_priority(text: str) -> str:
    """
    Priority based on urgency cues (not category).
    This makes priority prediction non-trivial and more realistic.
    """
    t = text.lower()

    # High if strong urgency
    if any(w in t for w in ["urgent", "asap", "immediately"]) or "deadline" in t or "tomorrow" in t:
        return "High"

    # Medium if error/failure keywords
    if any(w in t for w in ["failed", "error", "declined", "not working", "timeout", "can't access"]):
        return "Medium"

    return "Low"


def maybe_add_noise(text: str, rng: random.Random) -> str:
    """
    Add shared phrase overlap + occasional deadline context.
    """
    # 70% chance add a shared phrase (overlap across categories)
    if rng.random() < 0.7:
        text = f"{text} {rng.choice(SHARED_PHRASES)}"

    # 35% chance add deadline context
    if rng.random() < 0.35:
        text = f"{text} {rng.choice(DEADLINE_CONTEXT)}"

    return text


def maybe_mislabel_category(true_category: str, rng: random.Random) -> str:
    """
    Introduce realistic labeling noise (humans make mistakes).
    8% chance to mislabel into a nearby category.
    """
    if rng.random() > 0.08:
        return true_category

    confusion_map = {
        "IT": ["Fees", "Timetable"],
        "Fees": ["IT", "General"],
        "Timetable": ["IT", "General"],
        "Exams": ["General", "Timetable"],
        "General": ["IT", "Fees"],
    }
    return rng.choice(confusion_map[true_category])


def generate_and_store_tickets(n_samples=300, seed=42):
    rng = random.Random(seed)
    base_time = datetime.now(timezone.utc) - timedelta(days=30)

    for _ in range(n_samples):
        true_category = rng.choice(CATEGORIES)
        text = rng.choice(TEMPLATES[true_category])

        # Add overlap/noise to text
        text = maybe_add_noise(text, rng)

        # Priority based on urgency cues
        true_priority = assign_priority(text)

        # Optional label noise (makes classification imperfect)
        stored_category = maybe_mislabel_category(true_category, rng)

        created_at = base_time + timedelta(
            days=rng.randint(0, 29),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )

        ticket_id = str(uuid.uuid4())[:8]

        insert_ticket(
            ticket_id=ticket_id,
            text=text,
            true_category=stored_category,
            true_priority=true_priority,
            created_at=created_at
        )

    print(f"Inserted {n_samples} synthetic tickets into database.")


if __name__ == "__main__":
    generate_and_store_tickets(n_samples=400, seed=7)
