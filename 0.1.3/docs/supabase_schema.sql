-- Supabase PostgreSQL schema for Vox app

CREATE TABLE IF NOT EXISTS users (
    session_id UUID PRIMARY KEY,
    user_name TEXT NOT NULL,
    user_pronouns TEXT NOT NULL,
    target_gender TEXT DEFAULT 'unspecified'
);

CREATE TABLE IF NOT EXISTS vocal_data (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES users(session_id) ON DELETE CASCADE,
    timestamp TIMESTAMP,
    pitch DOUBLE PRECISION,
    hnr DOUBLE PRECISION,
    harmonics JSONB,
    formants JSONB,
    recording_path TEXT
);
