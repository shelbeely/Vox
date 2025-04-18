from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import JSONResponse
from vox.limiter import limiter
router = APIRouter()

# Dependency to get db_pool from app state
def get_db_pool(request: Request):
    return request.app.state.db_pool

@router.post("/set_target_gender", response_class=JSONResponse)
@limiter.limit("50/hour")
async def set_target_gender(request: Request, db_pool=Depends(get_db_pool)):
    session = request.session
    sid = session.get('id', 'default')
    data = await request.json()
    target_gender = data.get("target", "unspecified").strip()

    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET target_gender = $1 WHERE session_id = $2",
            target_gender, sid
        )

    request.app.state.logger.info(f"Session {sid} - set_target_gender: {target_gender}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "target_gender": target_gender}
    )

@router.post("/set_user_info", response_class=JSONResponse)
@limiter.limit("50/hour")
async def set_user_info(request: Request, db_pool=Depends(get_db_pool)):
    session = request.session
    sid = session.get('id', 'default')
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
        await conn.execute(
            "INSERT INTO users (session_id, user_name, user_pronouns) VALUES ($1, $2, $3) "
            "ON CONFLICT (session_id) DO UPDATE SET user_name = EXCLUDED.user_name, user_pronouns = EXCLUDED.user_pronouns",
            sid, user_name, user_pronouns
        )

    request.app.state.logger.info(f"Session {sid} - set_user_info: Name: {user_name}, Pronouns: {user_pronouns}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "user_name": user_name, "pronouns": user_pronouns}
    )

@router.get("/get_performances", response_class=JSONResponse)
async def get_performances(request: Request, db_pool=Depends(get_db_pool)):
    session = request.session
    sid = session.get('id', 'default')
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT timestamp, pitch, hnr, harmonics, formants, recording_path FROM vocal_data WHERE session_id = $1 ORDER BY timestamp DESC",
            sid
        )
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
async def profile(request: Request, db_pool=Depends(get_db_pool)):
    session = request.session
    sid = session.get('id')
    async with db_pool.acquire() as conn:
        if request.method == 'GET':
            user = await conn.fetchrow("SELECT * FROM users WHERE session_id = $1", sid)
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
            params.append(sid)
            query = f"UPDATE users SET {', '.join(updates)} WHERE session_id = ${len(params)}"
            await conn.execute(query, *params)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={'status': 'success', 'message': 'Profile updated'}
            )
