import uuid
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import JSONResponse
from vox.limiter import limiter

router = APIRouter()


def get_db_pool(request: Request):
    """Dependency to get db_pool from app state."""
    return request.app.state.db_pool


def get_session_id(request: Request) -> str:
    """Check if the session id already exists, if not create a new one."""
    sid = request.session.get("id")
    if not sid:
        sid = str(uuid.uuid4())
        request.session["id"] = sid
    return sid


@router.post("/set_target_gender", response_class=JSONResponse)
@limiter.limit("50/hour")
async def set_target_gender(request: Request, sid: str = Depends(get_session_id), db_pool=Depends(get_db_pool)):
    data = await request.json()
    target_gender = data.get("target", "unspecified").strip()

    async with db_pool.acquire() as conn:
        # Update by user_id from session
        session_row = await conn.fetchrow("SELECT user_id FROM sessions WHERE session_id = $1", sid)
        if session_row:
            await conn.execute(
                "UPDATE users SET target_gender = $1 WHERE user_id = $2",
                target_gender, session_row["user_id"]
            )

    request.app.state.logger.info(f"Session {sid} - set_target_gender: {target_gender}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "target_gender": target_gender}
    )


@router.post("/set_user_info", response_class=JSONResponse)
@limiter.limit("50/hour")
async def set_user_info(request: Request, sid: str = Depends(get_session_id), db_pool=Depends(get_db_pool)):
    data = await request.json()
    user_name = data.get("name", "friend").strip()[:50]
    user_pronouns = data.get("pronouns", "they/them/theirs/themselves").strip()

    if not user_name:
        request.app.state.logger.error(f"Session {sid} - set_user_info failed: Name cannot be empty")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Name cannot be empty"}
        )

    async with db_pool.acquire() as conn:
        # Set user info by user_id from session
        session_row = await conn.fetchrow("SELECT user_id FROM sessions WHERE session_id = $1", sid)
        if session_row:
            await conn.execute(
                "UPDATE users SET user_name = $1, user_pronouns = $2 WHERE user_id = $3",
                user_name, user_pronouns, session_row["user_id"]
            )

    request.app.state.logger.info(f"Session {sid} - set_user_info: Name: {user_name}, Pronouns: {user_pronouns}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "user_name": user_name, "pronouns": user_pronouns}
    )


@router.get("/get_performances", response_class=JSONResponse)
async def get_performances(request: Request, sid: str = Depends(get_session_id), db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as conn:
        # Look up user_id from session
        session_row = await conn.fetchrow("SELECT user_id FROM sessions WHERE session_id = $1", sid)
        user_id = session_row["user_id"] if session_row else None
        if user_id:
            rows = await conn.fetch(
                "SELECT timestamp, pitch, hnr, harmonics, formants, recording_path FROM vocal_data WHERE user_id = $1 ORDER BY timestamp DESC",
                user_id
            )
        else:
            rows = []
    performances = [
        {
            "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
            "pitch": row['pitch'],
            "hnr": row['hnr'],
            "harmonics": row['harmonics'],
            "formants": row['formants'],
            "recording_path": row['recording_path']
        }
        for row in rows
    ]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=performances
    )


@router.api_route("/profile", methods=["GET", "POST"], response_class=JSONResponse)
async def profile(request: Request, sid: str = Depends(get_session_id), db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as conn:
        if request.method == 'GET':
            # Fetch user by user_id from session
            session_row = await conn.fetchrow("SELECT user_id FROM sessions WHERE session_id = $1", sid)
            if not session_row:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={'status': 'error', 'message': 'User not found'}
                )
            user = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", session_row["user_id"])
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={'status': 'error', 'message': 'User not found'}
                )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    'status': 'success',
                    'email': user['email'],
                    'email_verified': user['email_verified'],
                    'discord_id': user['discord_id'],
                    'user_name': user['user_name'],
                    'user_pronouns': user['user_pronouns']
                }
            )
        else:
            data = await request.json()
            user_name = data.get('name')
            user_pronouns = data.get('pronouns')
            updates = []
            params = []
            if user_name:
                updates.append("user_name = $%d" % (len(params)+1))
                params.append(user_name)
            if user_pronouns:
                updates.append("user_pronouns = $%d" % (len(params)+1))
                params.append(user_pronouns)
            if not updates:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={'status': 'error', 'message': 'No updates provided'}
                )
            # Update by user_id from session
            session_row = await conn.fetchrow("SELECT user_id FROM sessions WHERE session_id = $1", sid)
            if not session_row:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={'status': 'error', 'message': 'User not found'}
                )
            params.append(session_row["user_id"])
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ${len(params)}"
            await conn.execute(query, *params)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={'status': 'success', 'message': 'Profile updated'}
            )
