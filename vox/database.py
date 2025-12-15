import json
from datetime import datetime, timedelta

# --- Persistent Session Management ---

async def create_session(db, session_id, user_id=None, expires_days=30, data=None):
    """
    Create a new session in the database.
    """
    expires_at = datetime.utcnow() + timedelta(days=expires_days)
    await db.execute(
        "INSERT INTO sessions (session_id, user_id, created_at, expires_at, data) VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)",
        (session_id, user_id, expires_at.isoformat(), json.dumps(data) if data else None)
    )
    await db.commit()

async def get_session(db, session_id):
    """
    Retrieve a session by session_id.
    """
    async with db.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)) as cursor:
        row = await cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None

async def update_session(db, session_id, data=None, expires_days=None):
    """
    Update session data and/or expiration.
    """
    if data is not None and expires_days is not None:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        await db.execute(
            "UPDATE sessions SET data = ?, expires_at = ? WHERE session_id = ?",
            (json.dumps(data), expires_at.isoformat(), session_id)
        )
    elif data is not None:
        await db.execute(
            "UPDATE sessions SET data = ? WHERE session_id = ?",
            (json.dumps(data), session_id)
        )
    elif expires_days is not None:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        await db.execute(
            "UPDATE sessions SET expires_at = ? WHERE session_id = ?",
            (expires_at.isoformat(), session_id)
        )
    await db.commit()

async def delete_session(db, session_id):
    """
    Delete a session from the database.
    """
    await db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    await db.commit()

async def cleanup_expired_sessions(db):
    """
    Delete all expired sessions.
    """
    await db.execute("DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP")
    await db.commit()

# --- Existing Vocal Data Logic ---

async def save_vocal_data_async(db, sid, timestamp, pitch, hnr, harmonics, formants, jitter_shimmer, praat_report, logger=None):
    """
    Save vocal analysis data asynchronously.
    """
    try:
        await db.execute(
            "INSERT INTO vocal_data (session_id, timestamp, pitch, hnr, harmonics, formants, jitter_shimmer, praat_report, recording_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)",
            (sid, timestamp, float(pitch), float(hnr), json.dumps(harmonics), json.dumps(formants), json.dumps(jitter_shimmer), praat_report)
        )
        await db.commit()
    except Exception as e:
        if logger:
            logger.error(f"DB insert error (likely missing columns): {e}")
        # fallback: insert without new columns
        try:
            await db.execute(
                "INSERT INTO vocal_data (session_id, timestamp, pitch, hnr, harmonics, formants, recording_path) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (sid, timestamp, float(pitch), float(hnr), json.dumps(harmonics), json.dumps(formants))
            )
            await db.commit()
        except Exception as e2:
            if logger:
                logger.error(f"Fallback DB insert error: {e2}")

async def update_recording_path_async(db, sid, timestamp, recording_path):
    """
    Update the database record with the saved file path.
    """
    await db.execute(
        "UPDATE vocal_data SET recording_path = ? WHERE session_id = ? AND timestamp = ?",
        (recording_path, sid, timestamp)
    )
    await db.commit()

# --- Chat Message Logic ---

async def save_chat_message_async(db, session_id, user_role, message, timestamp=None):
    """
    Save a chat message to the database.
    """
    if timestamp:
        await db.execute(
            "INSERT INTO chat_messages (session_id, user_role, message, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, user_role, message, timestamp)
        )
    else:
        await db.execute(
            "INSERT INTO chat_messages (session_id, user_role, message) VALUES (?, ?, ?)",
            (session_id, user_role, message)
        )
    await db.commit()

async def fetch_chat_history_async(db, session_id, limit=50):
    """
    Fetch the most recent chat messages for a session, ordered oldest to newest.
    """
    async with db.execute(
        "SELECT user_role, message, timestamp FROM chat_messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
        (session_id, limit)
    ) as cursor:
        rows = await cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        # Return in chronological order
        return list(reversed([dict(zip(columns, row)) for row in rows]))
