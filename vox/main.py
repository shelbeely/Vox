from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import HTMLResponse
from vox.fastapi_app import templates
import uuid
import asyncio

from starlette.responses import RedirectResponse
from vox.database import create_session, get_session

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    When you visit Vox, this is the first warm hug you get.
    It creates a unique session just for you, or welcomes you back if you've been here before.
    It also makes sure your name and pronouns are saved (or defaulted to 'friend' and 'they/them'),
    so every interaction feels personal and affirming.
    """
    app = request.app
    pool = getattr(app.state, "db_pool", None)
    logger = getattr(app.state, "logger", None)

    if pool is None:
        # Should not happen if startup event is set up correctly
        from vox.fastapi_app import startup_event
        await startup_event()

    # Persistent session management using database
    sid = request.cookies.get("session_id")
    session_obj = None
    if sid:
        session_obj = await get_session(pool, sid)
    if not session_obj:
        sid = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        # Create user first
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (user_id, user_name, user_pronouns) VALUES ($1, $2, $3)",
                user_id, "friend", "they/them/theirs/themselves"
            )
        await create_session(pool, sid, user_id=user_id)
        new_session = True
    else:
        new_session = False

    async with pool.acquire() as conn:
        # Fetch user by session from sessions table, then get user info
        session_row = await conn.fetchrow("SELECT user_id FROM sessions WHERE session_id = $1", sid)
        user = None
        if session_row and session_row["user_id"]:
            user = await conn.fetchrow("SELECT user_name, user_pronouns FROM users WHERE user_id = $1", session_row["user_id"])

    if logger:
        user_name = user["user_name"] if user and "user_name" in user else "friend"
        logger.info(f"Session {sid} - login: User '{user_name}' accessed Vox")

    response = templates.TemplateResponse("index.html", {"request": request})
    # Set session cookie if new
    if new_session:
        response.set_cookie("session_id", sid, max_age=2592000, httponly=True)
    return response
