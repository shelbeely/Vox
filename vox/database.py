import json
from datetime import datetime, timedelta

# --- User Preferences ---

async def get_user_preferences(db):
    """Get the single user's preferences."""
    async with db.execute("SELECT * FROM user_preferences WHERE id = 1") as cursor:
        row = await cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None

async def update_user_preferences(db, user_name=None, user_pronouns=None, target_gender=None):
    """Update user preferences."""
    updates = []
    params = []
    
    if user_name is not None:
        updates.append("user_name = ?")
        params.append(user_name)
    if user_pronouns is not None:
        updates.append("user_pronouns = ?")
        params.append(user_pronouns)
    if target_gender is not None:
        updates.append("target_gender = ?")
        params.append(target_gender)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE user_preferences SET {', '.join(updates)} WHERE id = 1"
        await db.execute(query, tuple(params))
        await db.commit()

# --- Vocal Data Logic ---

async def save_vocal_data_async(db, timestamp, pitch, hnr, harmonics, formants, jitter_shimmer, praat_report, logger=None):
    """
    Save vocal analysis data asynchronously.
    """
    try:
        await db.execute(
            "INSERT INTO vocal_data (timestamp, pitch, hnr, harmonics, formants, jitter_shimmer, praat_report, recording_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
            (timestamp, float(pitch), float(hnr), json.dumps(harmonics), json.dumps(formants), json.dumps(jitter_shimmer), praat_report)
        )
        await db.commit()
    except Exception as e:
        if logger:
            logger.error(f"DB insert error (likely missing columns): {e}")
        # fallback: insert without new columns
        try:
            await db.execute(
                "INSERT INTO vocal_data (timestamp, pitch, hnr, harmonics, formants, recording_path) "
                "VALUES (?, ?, ?, ?, ?, NULL)",
                (timestamp, float(pitch), float(hnr), json.dumps(harmonics), json.dumps(formants))
            )
            await db.commit()
        except Exception as e2:
            if logger:
                logger.error(f"Fallback DB insert error: {e2}")

async def update_recording_path_async(db, timestamp, recording_path):
    """
    Update the database record with the saved file path.
    """
    await db.execute(
        "UPDATE vocal_data SET recording_path = ? WHERE timestamp = ?",
        (recording_path, timestamp)
    )
    await db.commit()

async def get_all_vocal_data(db):
    """Get all vocal data ordered by timestamp."""
    async with db.execute(
        "SELECT timestamp, pitch, hnr, harmonics, formants, recording_path, transformed_path FROM vocal_data ORDER BY timestamp DESC"
    ) as cursor:
        rows = await cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def delete_all_vocal_data(db):
    """Delete all vocal data."""
    await db.execute("DELETE FROM vocal_data")
    await db.commit()

# --- Chat Message Logic ---

async def save_chat_message_async(db, user_role, message, timestamp=None):
    """
    Save a chat message to the database.
    """
    if timestamp:
        await db.execute(
            "INSERT INTO chat_messages (user_role, message, timestamp) VALUES (?, ?, ?)",
            (user_role, message, timestamp)
        )
    else:
        await db.execute(
            "INSERT INTO chat_messages (user_role, message) VALUES (?, ?)",
            (user_role, message)
        )
    await db.commit()

async def fetch_chat_history_async(db, limit=50):
    """
    Fetch the most recent chat messages, ordered oldest to newest.
    """
    async with db.execute(
        "SELECT user_role, message, timestamp FROM chat_messages ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    ) as cursor:
        rows = await cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        # Return in chronological order
        return list(reversed([dict(zip(columns, row)) for row in rows]))

