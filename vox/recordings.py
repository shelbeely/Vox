from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter
import typing as _t
import os
from datetime import datetime
import asyncio

from vox.limiter import limiter

router = APIRouter()

@router.post("/save_recording")
@limiter.limit("50/hour")
async def save_recording(
    request: Request,
    recording: UploadFile = File(...),
    timestamp: str = Form(None),
    apply_gender_transform: str = Form("false")
):
    session = request.session
    sid = session.get("id", "default")
    pool = request.app.state.db_pool
    # Look up user_id from session
    async with pool.acquire() as conn:
        session_row = await conn.fetchrow("SELECT user_id FROM sessions WHERE session_id = $1", sid)
        user_id = session_row["user_id"] if session_row else None
    if not recording:
        return JSONResponse({"status": "error", "message": "No recording file provided"}, status_code=400)

    if not timestamp:
        timestamp = datetime.now().isoformat()
    filename = f"{timestamp.replace(':', '-')}.wav"
    session_dir = os.path.join("recordings", sid)
    os.makedirs(session_dir, exist_ok=True)
    filepath = os.path.join(session_dir, filename)
    with open(filepath, "wb") as f:
        f.write(await recording.read())

    transformed_filepath = None

    if apply_gender_transform.lower() == "true":
        pool = request.app.state.db_pool
        async with pool.acquire() as conn:
            user_row = await conn.fetchrow(
                "SELECT target_gender FROM users WHERE session_id = $1",
                sid
            )
        target_gender = user_row["target_gender"] if user_row and user_row["target_gender"] else "unspecified"

        transformed_filename = filename.replace(".wav", "_gendered.wav")
        transformed_filepath = os.path.join(session_dir, transformed_filename)

        try:
            from gender_transform import transform_audio_to_gender
            transform_audio_to_gender(filepath, transformed_filepath, target_gender)
        except Exception as e:
            import logging
            logging.error(f"Gender transform error: {e}")
            transformed_filepath = None

    # Insert vocal_data with user_id and session_id
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO vocal_data (user_id, session_id, timestamp, pitch, hnr, harmonics, formants, recording_path) "
            "VALUES ($1, $2, $3, NULL, NULL, NULL, NULL, $4)",
            user_id, sid, timestamp, filepath
        )
        if transformed_filepath:
            try:
                await conn.execute(
                    "UPDATE vocal_data SET transformed_path = $1 WHERE user_id = $2 AND session_id = $3 AND timestamp = $4",
                    transformed_filepath, user_id, sid, timestamp
                )
            except Exception:
                pass

    logger = request.app.state.logger
    logger.info(f"Session {sid} - save_recording: saved at {filepath}, transformed: {transformed_filepath}")
    return {
        "status": "success",
        "recording_path": f"/recordings/{sid}/{filename}",
        "transformed_path": f"/recordings/{sid}/{transformed_filename}" if transformed_filepath else None
    }


@router.post("/clear_history")
@limiter.limit("50/hour")
async def clear_history(request: Request):
    session = request.session
    sid = session.get("id", "default")

    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT recording_path FROM vocal_data WHERE session_id = $1",
            sid
        )
        await conn.execute(
            "DELETE FROM vocal_data WHERE session_id = $1",
            sid
        )

    for row in rows:
        path = row["recording_path"]
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    session_dir = os.path.join("recordings", sid)
    if os.path.exists(session_dir):
        try:
            for file in os.listdir(session_dir):
                os.remove(os.path.join(session_dir, file))
            os.rmdir(session_dir)
        except Exception:
            pass

    logger = request.app.state.logger
    logger.info(f"Session {sid} - clear_history: cleared all recordings and data")
    return {"status": "success"}


@router.post("/convert_recordings")
@limiter.limit("50/hour")
async def convert_recordings(request: Request):
    session = request.session
    sid = session.get("id", "default")
    data = await request.json()
    paths = data.get("paths", [])

    if not paths:
        return JSONResponse({"status": "error", "message": "No recordings provided"}, status_code=400)

    pool = request.app.state.db_pool
    async with pool.acquire() as conn:
        user_row = await conn.fetchrow(
            "SELECT target_gender FROM users WHERE session_id = $1",
            sid
        )
    target_gender = user_row["target_gender"] if user_row and user_row["target_gender"] else "unspecified"

    from gender_transform import transform_audio_to_gender

    for original_path in paths:
        try:
            if not original_path.endswith(".wav"):
                continue
            transformed_path = original_path.replace(".wav", "_gendered.wav")
            if os.path.exists(transformed_path):
                continue

            transform_audio_to_gender(original_path, transformed_path, target_gender)

            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE vocal_data SET transformed_path = $1 WHERE session_id = $2 AND recording_path = $3",
                    transformed_path, sid, original_path
                )
        except Exception as e:
            import logging
            logging.error(f"Error converting {original_path}: {e}")

    return {"status": "success"}
