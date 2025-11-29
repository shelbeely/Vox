"""
CSRF Protection for FastAPI

This module provides CSRF (Cross-Site Request Forgery) protection for the Vox application.
It uses signed tokens to validate that form submissions originate from the application.
"""
import os
import secrets
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException, status
from functools import wraps

# Get secret key from environment - required for security
SECRET_KEY = os.environ.get("FASTAPI_SECRET_KEY")
if not SECRET_KEY:
    import warnings
    warnings.warn("FASTAPI_SECRET_KEY not set. Using random key - sessions will not persist across restarts.")
    SECRET_KEY = secrets.token_hex(32)

CSRF_TOKEN_MAX_AGE = 3600  # Token valid for 1 hour

serializer = URLSafeTimedSerializer(SECRET_KEY, salt="csrf-token")


def generate_csrf_token(session_id: str) -> str:
    """
    Generate a CSRF token tied to a session ID.
    The token includes a random component and is signed with a timestamp.
    """
    random_component = secrets.token_hex(16)
    data = f"{session_id}:{random_component}"
    return serializer.dumps(data)


def validate_csrf_token(token: str, session_id: str) -> bool:
    """
    Validate a CSRF token against the session ID.
    Returns True if valid, False otherwise.
    """
    try:
        data = serializer.loads(token, max_age=CSRF_TOKEN_MAX_AGE)
        token_session_id, _ = data.split(":", 1)
        return token_session_id == session_id
    except (BadSignature, SignatureExpired, ValueError):
        return False


async def get_csrf_token(request: Request) -> str:
    """
    Get or generate a CSRF token for the current session.
    The token is stored in the session for reuse.
    """
    session = request.session
    session_id = session.get("id")
    
    if not session_id:
        # Generate a temporary session ID for CSRF purposes
        session_id = secrets.token_hex(16)
        session["id"] = session_id
    
    # Check if we already have a valid token
    existing_token = session.get("csrf_token")
    if existing_token and validate_csrf_token(existing_token, session_id):
        return existing_token
    
    # Generate a new token
    new_token = generate_csrf_token(session_id)
    session["csrf_token"] = new_token
    return new_token


async def verify_csrf_token(request: Request) -> bool:
    """
    Verify the CSRF token from the request.
    Checks both form data and headers (for AJAX requests).
    """
    session = request.session
    session_id = session.get("id")
    
    if not session_id:
        # No session means no valid CSRF context
        return False
    
    # Try to get token from form data
    token = None
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        # For JSON requests, check the header
        token = request.headers.get("X-CSRF-Token")
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        # For form submissions, check form data
        form = await request.form()
        token = form.get("csrf_token")
    
    # Also check header as fallback for all request types
    if not token:
        token = request.headers.get("X-CSRF-Token")
    
    if not token:
        return False
    
    return validate_csrf_token(token, session_id)


def csrf_protect(func):
    """
    Decorator to protect a route with CSRF validation.
    Use on POST, PUT, DELETE endpoints that modify data.
    """
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        if not await verify_csrf_token(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing or invalid"
            )
        return await func(request, *args, **kwargs)
    return wrapper
