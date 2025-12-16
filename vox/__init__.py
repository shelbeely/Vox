import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Setup logging (shared for FastAPI)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# NOTE: All Flask app, SocketIO, CSRF, Limiter, and Blueprint logic has been removed.
# FastAPI app is now the main entry point (see vox/fastapi_app.py).

