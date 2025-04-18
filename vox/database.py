import json
from datetime import datetime, timedelta

# --- Persistent Session Management ---

async def create_session(db_pool, session_id, user_id=None, expires_days=30, data=None):
    """
    Create a new session in the database.
    """
    expires_at = datetime.utcnow() + timedelta(days=expires_days)
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO sessions (session_id, user_id, created_at, expires_at, data) VALUES ($1, $2, now(), $3, $4)",
            session_id, user_id, expires_at, json.dumps(data) if data else None
        )

async def get_session(db_pool, session_id):
    """
    Retrieve a session by session_id.
    """
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM sessions WHERE session_id = $1", session_id)

async def update_session(db_pool, session_id, data=None, expires_days=None):
    """
    Update session data and/or expiration.
    """
    async with db_pool.acquire() as conn:
        if data is not None and expires_days is not None:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
            await conn.execute(
                "UPDATE sessions SET data = $1, expires_at = $2 WHERE session_id = $3",
                json.dumps(data), expires_at, session_id
            )
        elif data is not None:
            await conn.execute(
                "UPDATE sessions SET data = $1 WHERE session_id = $2",
                json.dumps(data), session_id
            )
        elif expires_days is not None:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
            await conn.execute(
                "UPDATE sessions SET expires_at = $1 WHERE session_id = $2",
                expires_at, session_id
            )

async def delete_session(db_pool, session_id):
    """
    Delete a session from the database.
    """
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM sessions WHERE session_id = $1", session_id)

async def cleanup_expired_sessions(db_pool):
    """
    Delete all expired sessions.
    """
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM sessions WHERE expires_at < now()")

# --- Existing Vocal Data Logic ---

async def save_vocal_data_async(db_pool, sid, timestamp, pitch, hnr, harmonics, formants, jitter_shimmer, praat_report, logger=None):
    """
    Save vocal analysis data asynchronously.
    """
    async with db_pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO vocal_data (session_id, timestamp, pitch, hnr, harmonics, formants, jitter_shimmer, praat_report, recording_path) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NULL)",
                sid, timestamp, float(pitch), float(hnr), json.dumps(harmonics), json.dumps(formants), json.dumps(jitter_shimmer), praat_report
            )
        except Exception as e:
            if logger:
                logger.error(f"DB insert error (likely missing columns): {e}")
            # fallback: insert without new columns
            try:
                await conn.execute(
                    "INSERT INTO vocal_data (session_id, timestamp, pitch, hnr, harmonics, formants, recording_path) "
                    "VALUES ($1, $2, $3, $4, $5, $6, NULL)",
                    sid, timestamp, float(pitch), float(hnr), json.dumps(harmonics), json.dumps(formants)
                )
            except Exception as e2:
                if logger:
                    logger.error(f"Fallback DB insert error: {e2}")

async def update_recording_path_async(db_pool, sid, timestamp, recording_path):
    """
    Update the database record with the saved file path.
    """
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE vocal_data SET recording_path = $1 WHERE session_id = $2 AND timestamp = $3",
            recording_path, sid, timestamp
        )
