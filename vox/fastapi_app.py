import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from vox.templates import templates
from starlette.middleware.sessions import SessionMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from vox.limiter import limiter

import asyncio

# Routers (to be implemented in each module)
from vox.main import router as main_router
from vox.recordings import router as recordings_router
from vox.chat import router as chat_router
from vox.user import router as user_router
from vox.auth import router as auth_router

app = FastAPI()

# Secret key for session middleware
SECRET_KEY = os.environ.get("FASTAPI_SECRET_KEY", "default_secret_key")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "../static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
app.state.logger = logger

# Database pool (asyncpg)
app.state.db_pool = None

@app.on_event("startup")
async def startup_event():
    import asyncpg
    SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL")
    app.state.db_pool = await asyncpg.create_pool(SUPABASE_DB_URL, max_size=10, statement_cache_size=0)
    # Patch db_pool into routers if needed

# Register routers
app.include_router(main_router)
app.include_router(user_router, prefix="/user")
app.include_router(auth_router, prefix="/auth")
app.include_router(recordings_router, prefix="/recordings")
app.include_router(chat_router, prefix="/chat")

# Error handlers (example for 404)
from fastapi.responses import JSONResponse
from fastapi.requests import Request as FastAPIRequest

@app.exception_handler(404)
async def not_found_handler(request: FastAPIRequest, exc):
    return JSONResponse(status_code=404, content={"status": "error", "message": "Not found"})

@app.exception_handler(500)
async def server_error_handler(request: FastAPIRequest, exc):
    return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

import socketio

# --- Socket.IO integration ---
# Create an AsyncServer with ASGI mode
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# Create the ASGI app for Socket.IO
sio_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Export sio and db_pool for use in handlers
def get_socketio():
    return sio

def get_db_pool():
    return app.state.db_pool

# Note: You should now run with:
# hypercorn vox.fastapi_app:sio_app --bind 0.0.0.0:3000

# Import socketio event handlers to register them
import vox.socketio_handlers
