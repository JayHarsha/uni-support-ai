# 🎓 University Support AI System

An engineered AI-based ticket classification system designed to reduce pressure on university support offices during peak periods (enrollment week, exam week).

The system automatically:

- Classifies support tickets into predefined categories
- Assigns priority levels
- Logs high-priority events
- Monitors model performance
- Exposes a real-time API endpoint
- Orchestrates the full pipeline using Dagster
- Runs entirely via Docker for reproducibility

---

# 📌 Problem Statement

Students submit support requests such as:

- “I can’t access my Moodle”
- “My fee payment failed”
- “I need timetable help”
- “I have an exam deferral issue”
- “I forgot my password”

The system must:

1. Classify each request into one of:
   - IT
   - Fees
   - Timetable
   - Exams
   - General
2. Assign priority:
   - Low
   - Medium
   - High
3. Log events for high-priority tickets
4. Monitor model performance
5. Follow a structured SDLC process
6. Be reproducible and portable

---

# 🏗 Architecture Overview

The project follows a Layered Architecture with Event Simulation:

Layers:

1. Data Generation Layer (Synthetic Data → PostgreSQL)
2. Training Layer (TF-IDF + Logistic Regression)
3. Inference Layer (Prediction + Event Triggering)
4. Monitoring Layer (Evaluation + Drift Detection)
5. API Layer (FastAPI)
6. Orchestration Layer (Dagster)
7. Infrastructure Layer (Dockerized Services)

Flow:
User → FastAPI → ML Model → PostgreSQL → Event Log → Monitoring → Metrics

---

# 🧠 Machine Learning Approach

Feature Extraction:

- TF-IDF (Term Frequency–Inverse Document Frequency)

Model:

- Logistic Regression (multi-class classification)

Separate models are trained for:

- Category classification
- Priority classification

Evaluation Metrics:

- Accuracy
- Precision (macro)
- Recall (macro)
- F1-score (macro)
- Confusion Matrix
- Average Confidence
- Confidence Drift Over Time

---

# ⚙ Technology Stack

ML & Data:

- Python
- NumPy
- Pandas
- Scikit-learn
- Joblib

Backend:

- FastAPI
- Uvicorn

Orchestration:

- Dagster

Database:

- PostgreSQL (Dockerized)

Infrastructure:

- Docker
- Docker Compose

Event Simulation:

- Python Queue
- Database Event Logging

```

# 📂 Project Structure

uni-support-ai/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── db_init.sql
├── dagster_pipeline.py
│
├── api/
│ └── main.py
│
├── src/
│ ├── config.py
│ ├── db.py
│ ├── data_generation.py
│ ├── train_model.py
│ ├── inference_service.py
│ ├── event_bus.py
│ └── monitoring.py
│
├── outputs/ (auto-generated)
│ ├── category_model.joblib
│ ├── priority_model.joblib
│ ├── predictions.csv
│ ├── events.log
│ ├── metrics.json
│ ├── confusion_matrix.csv
│ ├── high_priority_per_day.csv
│ └── drift_confidence_over_time.csv
│
└── README.md

```

# 🚀 How To Run (Fully Dockerized)

Prerequisite:

- Install Docker Desktop

Step 1: Clone the repository
git clone <repository_url>
cd uni-support-ai

Step 2: Build and start all services
docker compose up -d --build

This will start:

- PostgreSQL → internal port 5432 (mapped to 5433 locally)
- FastAPI → http://localhost:8000
- Dagster UI → http://localhost:3000

---

# ▶ Run the Full Pipeline

Open:
http://localhost:3000

1. Go to "Assets"
2. Click "Materialize All"

This will execute:

- Synthetic data generation
- Model training
- Batch inference
- Monitoring & metric computation

---

# 🌐 Test the API

Open:
http://localhost:8000/docs

Use:
POST /predict

Example Request:
{
"text": "My fee payment failed and this is urgent"
}

Example Response:
{
"ticket_id": "abc12345",
"category": "Fees",
"priority": "High",
"confidence": 0.82,
"processed_at": "2026-02-16T21:15:00Z"
}

Behavior:

- All predictions are stored in the predictions table.
- If priority = High → event is logged in events table.
- Event is also written to events.log.

---

# 🗄 Database Details

Database Name:
uni_support_ai

Tables:

- tickets
- predictions
- events
- metrics

High-priority predictions trigger event creation.

---

# 📊 Monitoring Outputs

After pipeline execution, the following files are generated in outputs/:

- metrics.json
- confusion_matrix.csv
- high_priority_per_day.csv
- drift_confidence_over_time.csv

Monitoring computes:

- Category Accuracy
- Macro Precision
- Macro Recall
- Macro F1-score
- Average Confidence
- Per-class performance
- Confidence drift per day

Example baseline performance:

- Category Accuracy ≈ 0.92
- Macro F1 ≈ 0.91
- Balanced performance across 5 categories

---

# 🔄 SDLC Process Followed

1. Planning:
   Defined classification and prioritization goals.

2. Requirements:
   Multi-class classification, priority assignment, monitoring.

3. Design:
   Layered architecture with event-driven simulation.

4. Implementation:
   Modular Python services with clear separation of concerns.

5. Testing:
   - Train-test split
   - API testing via Swagger/Postman
   - Monitoring metrics validation

6. Deployment:
   Fully containerized using Docker Compose.

7. Evolution:
   Drift detection and extensible pipeline via Dagster.

---

# 🐳 Why Docker?

Docker ensures:

- Environment consistency
- No local dependency conflicts
- Database isolation
- Reproducibility
- One-command deployment

Anyone can run:
docker compose up -d --build

No local PostgreSQL or Python installation required.

---

# 🔁 Reset System (If Needed)

To completely reset database and volumes:
docker compose down -v
docker compose up -d --build

---

# 🎯 End-to-End Flow Summary

User Request
↓
FastAPI Endpoint
↓
ML Model (TF-IDF + Logistic Regression)
↓
Prediction Stored in PostgreSQL
↓
High-Priority Event Logged
↓
Monitoring Layer Computes Metrics
↓
Dagster Orchestrates Full Pipeline

---

# ✅ Reproducibility

The system is fully portable and self-contained.

Steps:

1. Install Docker
2. Run docker compose up -d --build
3. Open Dagster UI and materialize
4. Test API via Swagger

No configuration changes required.

---
