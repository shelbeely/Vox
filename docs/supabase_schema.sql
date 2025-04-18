-- Supabase PostgreSQL schema for Vox app with Discord + Email/Password Auth (v0.1.6)

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID UNIQUE, -- link anonymous sessions
    user_name TEXT NOT NULL,
    user_pronouns TEXT NOT NULL,
    target_gender TEXT DEFAULT 'unspecified',
    email VARCHAR UNIQUE,
    password_hash VARCHAR,
    discord_id VARCHAR UNIQUE,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR,
    verification_token_expires TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vocal_data (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    session_id UUID, -- legacy support
    timestamp TIMESTAMP,
    pitch DOUBLE PRECISION,
    hnr DOUBLE PRECISION,
    harmonics JSONB,
    formants JSONB,
    jitter_shimmer JSONB,
    praat_report TEXT,
    recording_path TEXT
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_discord_id ON users(discord_id);
CREATE INDEX IF NOT EXISTS idx_vocal_data_user_id ON vocal_data(user_id);
CREATE INDEX IF NOT EXISTS idx_vocal_data_session_id ON vocal_data(session_id);

CREATE TABLE IF NOT EXISTS password_resets (
    email VARCHAR NOT NULL,
    token VARCHAR PRIMARY KEY,
    expires_at TIMESTAMP NOT NULL
);

-- Persistent session management
CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT now(),
    expires_at TIMESTAMP,
    data JSONB
);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
