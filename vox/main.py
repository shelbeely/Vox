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
        await create_session(pool, sid)
        new_session = True
    else:
        new_session = False

    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT user_name, user_pronouns FROM users WHERE session_id = $1", sid)
        if not user:
            await conn.execute(
                "INSERT INTO users (session_id, user_name, user_pronouns) VALUES ($1, $2, $3)",
                sid, "friend", "they/them/theirs/themselves"
            )

    if logger:
        logger.info(f"Session {sid} - login: User accessed Vox")

    response = templates.TemplateResponse("index.html", {"request": request})
    # Set session cookie if new
    if new_session:
        response.set_cookie("session_id", sid, max_age=2592000, httponly=True)
    return response
