-- SQLite schema for Vox app - Local-first single-user version

-- User preferences (single user)
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY CHECK (id = 1),  -- Ensure only one row
    user_name TEXT NOT NULL DEFAULT 'friend',
    user_pronouns TEXT NOT NULL DEFAULT 'they/them/theirs/themselves',
    target_gender TEXT DEFAULT 'unspecified',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default user preferences
INSERT OR IGNORE INTO user_preferences (id, user_name, user_pronouns, target_gender)
VALUES (1, 'friend', 'they/them/theirs/themselves', 'unspecified');

CREATE TABLE IF NOT EXISTS vocal_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,
    pitch REAL,
    hnr REAL,
    harmonics TEXT,
    formants TEXT,
    jitter_shimmer TEXT,
    praat_report TEXT,
    recording_path TEXT,
    transformed_path TEXT
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_vocal_data_timestamp ON vocal_data(timestamp);

-- Chat messages for real-time and history
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_role TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp);
