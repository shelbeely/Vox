from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from vox.templates import templates
from vox.database import get_user_preferences

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Welcome to Vox! This serves the main application page.
    In the local-first version, there's just one user, so we simply load their preferences
    and show the interface. No sessions or authentication needed.
    """
    app = request.app
    db = getattr(app.state, "db", None)
    logger = getattr(app.state, "logger", None)

    if db is None:
        # Should not happen if startup event is set up correctly
        from vox.fastapi_app import startup_event
        await startup_event()
        db = app.state.db

    # Get user preferences for logging
    user_prefs = await get_user_preferences(db)
    
    if logger:
        user_name = user_prefs['user_name'] if user_prefs else "friend"
        logger.info(f"User '{user_name}' accessed Vox")

    response = templates.TemplateResponse("index.html", {"request": request})
    return response
