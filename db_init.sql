-- Ensure we are using public schema explicitly
CREATE SCHEMA IF NOT EXISTS public;
SET search_path TO public;

-- ===============================
-- Drop tables if they exist
-- (development reset)
-- ===============================
DROP TABLE IF EXISTS public.metrics;
DROP TABLE IF EXISTS public.events;
DROP TABLE IF EXISTS public.predictions;
DROP TABLE IF EXISTS public.tickets;

-- ===============================
-- 1) Tickets Table
-- ===============================
CREATE TABLE public.tickets (
    ticket_id VARCHAR(20) PRIMARY KEY,
    text TEXT NOT NULL,
    true_category VARCHAR(50) NOT NULL,
    true_priority VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- 2) Predictions Table
-- ===============================
CREATE TABLE public.predictions (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(20) REFERENCES public.tickets(ticket_id) ON DELETE CASCADE,
    pred_category VARCHAR(50) NOT NULL,
    pred_priority VARCHAR(20) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- 3) Events Table
-- ===============================
CREATE TABLE public.events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- 4) Metrics Table
-- ===============================
CREATE TABLE public.metrics (
    id SERIAL PRIMARY KEY,
    category_accuracy DOUBLE PRECISION,
    precision_macro DOUBLE PRECISION,
    recall_macro DOUBLE PRECISION,
    f1_macro DOUBLE PRECISION,
    avg_confidence DOUBLE PRECISION,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===============================
-- Helpful Indexes
-- ===============================
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON public.tickets(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_ticket_id ON public.predictions(ticket_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON public.events(created_at);
