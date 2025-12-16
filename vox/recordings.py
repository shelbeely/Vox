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

def get_db(request: Request):
    """Dependency to get db from app state."""
    return request.app.state.db

@router.post("/save_recording")
@limiter.limit("50/hour")
async def save_recording(
    request: Request,
    recording: UploadFile = File(...),
    timestamp: str = Form(None),
    apply_gender_transform: str = Form("false"),
    db = Depends(get_db)
):
    if not recording:
        return JSONResponse({"status": "error", "message": "No recording file provided"}, status_code=400)

    if not timestamp:
        timestamp = datetime.now().isoformat()
    filename = f"{timestamp.replace(':', '-')}.wav"
    recordings_dir = "recordings"
    os.makedirs(recordings_dir, exist_ok=True)
    filepath = os.path.join(recordings_dir, filename)
    with open(filepath, "wb") as f:
        f.write(await recording.read())

    transformed_filepath = None

    if apply_gender_transform.lower() == "true":
        # Get user preferences
        from vox.database import get_user_preferences
        user_prefs = await get_user_preferences(db)
        target_gender = user_prefs['target_gender'] if user_prefs else "unspecified"

        transformed_filename = filename.replace(".wav", "_gendered.wav")
        transformed_filepath = os.path.join(recordings_dir, transformed_filename)

        try:
            from gender_transform import transform_audio_to_gender
            transform_audio_to_gender(filepath, transformed_filepath, target_gender)
        except Exception as e:
            import logging
            logging.error(f"Gender transform error: {e}")
            transformed_filepath = None

    await db.execute(
        "INSERT INTO vocal_data (timestamp, pitch, hnr, harmonics, formants, recording_path) "
        "VALUES (?, NULL, NULL, NULL, NULL, ?)",
        (timestamp, filepath)
    )
    await db.commit()
    
    if transformed_filepath:
        try:
            await db.execute(
                "UPDATE vocal_data SET transformed_path = ? WHERE timestamp = ?",
                (transformed_filepath, timestamp)
            )
            await db.commit()
        except Exception:
            pass

    logger = request.app.state.logger
    logger.info(f"save_recording: saved at {filepath}, transformed: {transformed_filepath}")
    return {
        "status": "success",
        "recording_path": f"/recordings/{filename}",
        "transformed_path": f"/recordings/{transformed_filename}" if transformed_filepath else None
    }


@router.post("/clear_history")
@limiter.limit("50/hour")
async def clear_history(request: Request, db = Depends(get_db)):
    async with db.execute("SELECT recording_path, transformed_path FROM vocal_data") as cursor:
        rows = await cursor.fetchall()
    
    await db.execute("DELETE FROM vocal_data")
    await db.commit()

    for row in rows:
        for path in [row[0], row[1]]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    # Clean up recordings directory
    recordings_dir = "recordings"
    if os.path.exists(recordings_dir):
        try:
            for file in os.listdir(recordings_dir):
                file_path = os.path.join(recordings_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception:
            pass

    logger = request.app.state.logger
    logger.info(f"clear_history: cleared all recordings and data")
    return {"status": "success"}


@router.post("/convert_recordings")
@limiter.limit("50/hour")
async def convert_recordings(request: Request, db = Depends(get_db)):
    data = await request.json()
    paths = data.get("paths", [])

    if not paths:
        return JSONResponse({"status": "error", "message": "No recordings provided"}, status_code=400)

    # Get user preferences
    from vox.database import get_user_preferences
    user_prefs = await get_user_preferences(db)
    target_gender = user_prefs['target_gender'] if user_prefs else "unspecified"

    from gender_transform import transform_audio_to_gender

    for original_path in paths:
        try:
            if not original_path.endswith(".wav"):
                continue
            transformed_path = original_path.replace(".wav", "_gendered.wav")
            if os.path.exists(transformed_path):
                continue

            transform_audio_to_gender(original_path, transformed_path, target_gender)

            # Extract timestamp from path for update
            filename = os.path.basename(original_path)
            timestamp = filename.replace(".wav", "").replace("-", ":")
            
            await db.execute(
                "UPDATE vocal_data SET transformed_path = ? WHERE recording_path = ?",
                (transformed_path, original_path)
            )
            await db.commit()
        except Exception as e:
            import logging
            logging.error(f"Error converting {original_path}: {e}")

    return {"status": "success"}
