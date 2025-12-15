import uuid
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import JSONResponse
from vox.limiter import limiter

router = APIRouter()


def get_db(request: Request):
    """Dependency to get db from app state."""
    return request.app.state.db


def get_session_id(request: Request) -> str:
    """Check if the session id already exists, if not create a new one."""
    sid = request.session.get("id")
    if not sid:
        sid = str(uuid.uuid4())
        request.session["id"] = sid
    return sid


@router.post("/set_target_gender", response_class=JSONResponse)
@limiter.limit("50/hour")
async def set_target_gender(request: Request, sid: str = Depends(get_session_id), db=Depends(get_db)):
    data = await request.json()
    target_gender = data.get("target", "unspecified").strip()

    # Update by user_id from session
    async with db.execute("SELECT user_id FROM sessions WHERE session_id = ?", (sid,)) as cursor:
        session_row = await cursor.fetchone()
    
    if session_row:
        await db.execute(
            "UPDATE users SET target_gender = ? WHERE user_id = ?",
            (target_gender, session_row[0])
        )
        await db.commit()

    request.app.state.logger.info(f"Session {sid} - set_target_gender: {target_gender}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "target_gender": target_gender}
    )


@router.post("/set_user_info", response_class=JSONResponse)
@limiter.limit("50/hour")
async def set_user_info(request: Request, sid: str = Depends(get_session_id), db=Depends(get_db)):
    data = await request.json()
    user_name = data.get("name", "friend").strip()[:50]
    user_pronouns = data.get("pronouns", "they/them/theirs/themselves").strip()

    if not user_name:
        request.app.state.logger.error(f"Session {sid} - set_user_info failed: Name cannot be empty")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Name cannot be empty"}
        )

    # Set user info by user_id from session
    async with db.execute("SELECT user_id FROM sessions WHERE session_id = ?", (sid,)) as cursor:
        session_row = await cursor.fetchone()
    
    if session_row:
        await db.execute(
            "UPDATE users SET user_name = ?, user_pronouns = ? WHERE user_id = ?",
            (user_name, user_pronouns, session_row[0])
        )
        await db.commit()

    request.app.state.logger.info(f"Session {sid} - set_user_info: Name: {user_name}, Pronouns: {user_pronouns}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "user_name": user_name, "pronouns": user_pronouns}
    )


@router.get("/get_performances", response_class=JSONResponse)
async def get_performances(request: Request, sid: str = Depends(get_session_id), db=Depends(get_db)):
    # Look up user_id from session
    async with db.execute("SELECT user_id FROM sessions WHERE session_id = ?", (sid,)) as cursor:
        session_row = await cursor.fetchone()
    
    user_id = session_row[0] if session_row else None
    
    if user_id:
        async with db.execute(
            "SELECT timestamp, pitch, hnr, harmonics, formants, recording_path FROM vocal_data WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
    else:
        rows = []
    
    performances = [
        {
            "timestamp": row[0],
            "pitch": row[1],
            "hnr": row[2],
            "harmonics": row[3],
            "formants": row[4],
            "recording_path": row[5]
        }
        for row in rows
    ]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=performances
    )


@router.api_route("/profile", methods=["GET", "POST"], response_class=JSONResponse)
async def profile(request: Request, sid: str = Depends(get_session_id), db=Depends(get_db)):
    if request.method == 'GET':
        # Fetch user by user_id from session
        async with db.execute("SELECT user_id FROM sessions WHERE session_id = ?", (sid,)) as cursor:
            session_row = await cursor.fetchone()
        
        if not session_row:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'status': 'error', 'message': 'User not found'}
            )
        
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (session_row[0],)) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                user = dict(zip(columns, row))
            else:
                user = None
        
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
                'email_verified': bool(user['email_verified']),
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
            updates.append("user_name = ?")
            params.append(user_name)
        if user_pronouns:
            updates.append("user_pronouns = ?")
            params.append(user_pronouns)
        
        if not updates:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'status': 'error', 'message': 'No updates provided'}
            )
        
        # Update by user_id from session
        async with db.execute("SELECT user_id FROM sessions WHERE session_id = ?", (sid,)) as cursor:
            session_row = await cursor.fetchone()
        
        if not session_row:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'status': 'error', 'message': 'User not found'}
            )
        
        params.append(session_row[0])
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
        await db.execute(query, tuple(params))
        await db.commit()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'status': 'success', 'message': 'Profile updated'}
        )
