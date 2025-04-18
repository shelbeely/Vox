import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Setup logging (shared for FastAPI)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Placeholder for asyncpg pool (legacy, not used in FastAPI app)
db_pool = None

async def init_pg_pool():
    import asyncpg
    global db_pool
    if db_pool is not None:
        return db_pool
    SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL")
    db_pool = await asyncpg.create_pool(SUPABASE_DB_URL, max_size=10, statement_cache_size=0)
    return db_pool

# NOTE: All Flask app, SocketIO, CSRF, Limiter, and Blueprint logic has been removed.
# FastAPI app is now the main entry point (see app/fastapi_app.py).
