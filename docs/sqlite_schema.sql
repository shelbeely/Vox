-- SQLite schema for Vox app - Local-first version
-- Migrated from PostgreSQL schema

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_name TEXT NOT NULL,
    user_pronouns TEXT NOT NULL,
    target_gender TEXT DEFAULT 'unspecified',
    email TEXT UNIQUE,
    password_hash TEXT,
    discord_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_verified INTEGER DEFAULT 0,
    verification_token TEXT,
    verification_token_expires TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vocal_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    session_id TEXT,
    timestamp TIMESTAMP,
    pitch REAL,
    hnr REAL,
    harmonics TEXT,
    formants TEXT,
    jitter_shimmer TEXT,
    praat_report TEXT,
    recording_path TEXT
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_discord_id ON users(discord_id);
CREATE INDEX IF NOT EXISTS idx_vocal_data_user_id ON vocal_data(user_id);
CREATE INDEX IF NOT EXISTS idx_vocal_data_session_id ON vocal_data(session_id);

CREATE TABLE IF NOT EXISTS password_resets (
    email TEXT NOT NULL,
    token TEXT PRIMARY KEY,
    expires_at TIMESTAMP NOT NULL
);

-- Persistent session management
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    data TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- Chat messages for real-time and history
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_role TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp);
