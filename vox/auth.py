from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import JSONResponse
import typing as _t
import os
import secrets
from datetime import datetime, timedelta
import asyncio

from vox.limiter import limiter

from email_utils import send_verification_email, send_password_reset_email

__all__ = ["router"]
router = APIRouter()

# Dependency to get db_pool from app state
def get_db_pool(request: Request):
    return request.app.state.db_pool

@router.post("/register", response_class=JSONResponse)
async def register(request: Request, db_pool=Depends(get_db_pool)):
    data = await request.json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    user_name = data.get('name', 'friend').strip()[:50]
    user_pronouns = data.get('pronouns', 'they/them/theirs/themselves').strip()

    if not email or not password:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'status': 'error', 'message': 'Email and password required'}
        )

    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        if existing:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'status': 'error', 'message': 'Email already registered'}
            )

        password_hash = await asyncio.to_thread(lambda: __import__('bcrypt').hashpw(password.encode(), __import__('bcrypt').gensalt()).decode())

        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=24)

        await conn.execute(
            "INSERT INTO users (email, password_hash, user_name, user_pronouns, verification_token, verification_token_expires) "
            "VALUES ($1, $2, $3, $4, $5, $6)",
            email, password_hash, user_name, user_pronouns, token, expires
        )

    send_verification_email(email, token)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'status': 'success', 'message': 'Registered. Please verify your email.'}
    )

@router.get("/verify_email", response_class=JSONResponse)
async def verify_email(request: Request, db_pool=Depends(get_db_pool)):
    token = request.query_params.get('token', '').strip()
    if not token:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'status': 'error', 'message': 'Missing token'}
        )

    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE verification_token = $1 AND verification_token_expires > now()", token
        )
        if not user:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'status': 'error', 'message': 'Invalid or expired token'}
            )

        await conn.execute(
            "UPDATE users SET email_verified = TRUE, verification_token = NULL, verification_token_expires = NULL WHERE user_id = $1",
            user['user_id']
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'status': 'success', 'message': 'Email verified successfully'}
    )

from vox.database import create_session
import uuid

@router.post("/login", response_class=JSONResponse)
async def login(request: Request, db_pool=Depends(get_db_pool)):
    data = await request.json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    print(data)
    if not email or not password:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'status': 'error', 'message': 'Email and password required'}
        )

    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'status': 'error', 'message': 'Invalid credentials'}
            )

        if not user['email_verified']:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={'status': 'error', 'message': 'Email not verified'}
            )

        valid = await asyncio.to_thread(lambda: __import__('bcrypt').checkpw(password.encode(), user['password_hash'].encode()))
        if not valid:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'status': 'error', 'message': 'Invalid credentials'}
            )

        # Create a new session for the user
        session_id = str(uuid.uuid4())
        await create_session(db_pool, session_id, user_id=user['user_id'])

        # Store session_id in the session middleware
        request.session['session_id'] = session_id
        request.session['user_id'] = user['user_id']

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'status': 'success', 'message': 'Logged in', 'session_id': session_id}
    )

@router.post("/request_password_reset", response_class=JSONResponse)
async def request_password_reset(request: Request, db_pool=Depends(get_db_pool)):
    data = await request.json()
    email = data.get('email', '').strip().lower()
    if not email:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'status': 'error', 'message': 'Email required'}
        )

    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={'status': 'success', 'message': 'If the email exists, a reset link was sent'}
            )

        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(hours=1)

        await conn.execute(
            "INSERT INTO password_resets (email, token, expires_at) VALUES ($1, $2, $3) "
            "ON CONFLICT (token) DO UPDATE SET expires_at = $3",
            email, token, expires
        )

    send_password_reset_email(email, token)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'status': 'success', 'message': 'If the email exists, a reset link was sent'}
    )

@router.post("/reset_password", response_class=JSONResponse)
async def reset_password(request: Request, db_pool=Depends(get_db_pool)):
    data = await request.json()
    token = data.get('token', '').strip()
    new_password = data.get('password', '').strip()

    if not token or not new_password:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'status': 'error', 'message': 'Token and new password required'}
        )

    async with db_pool.acquire() as conn:
        reset = await conn.fetchrow(
            "SELECT * FROM password_resets WHERE token = $1 AND expires_at > now()", token
        )
        if not reset:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'status': 'error', 'message': 'Invalid or expired token'}
            )

        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", reset['email'])
        if not user:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'status': 'error', 'message': 'User not found'}
            )

        password_hash = await asyncio.to_thread(lambda: __import__('bcrypt').hashpw(new_password.encode(), __import__('bcrypt').gensalt()).decode())

        await conn.execute(
            "UPDATE users SET password_hash = $1 WHERE email = $2",
            password_hash, reset['email']
        )
        await conn.execute("DELETE FROM password_resets WHERE token = $1", token)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'status': 'success', 'message': 'Password reset successful'}
    )

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5000/auth/discord/callback")

@router.get("/login/discord", response_class=JSONResponse)
async def login_discord():
    discord_oauth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20email"
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"redirect": discord_oauth_url}
    )

@router.get("/auth/discord/callback", response_class=JSONResponse)
async def discord_callback(request: Request, db_pool=Depends(get_db_pool)):
    import requests

    code = request.query_params.get('code')
    if not code:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'status': 'error', 'message': 'Missing code'}
        )

    token_url = "https://discord.com/api/oauth2/token"
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI,
        'scope': 'identify email'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    resp = requests.post(token_url, data=data, headers=headers)
    if resp.status_code != 200:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'status': 'error', 'message': 'Failed to get token'}
        )
    token_json = resp.json()
    access_token = token_json.get('access_token')

    user_resp = requests.get(
        "https://discord.com/api/users/@me",
        headers={'Authorization': f'Bearer {access_token}'}
    )
    if user_resp.status_code != 200:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'status': 'error', 'message': 'Failed to fetch user info'}
        )
    user_json = user_resp.json()
    discord_id = user_json['id']
    email = user_json.get('email')

    session = request.session
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE discord_id = $1", discord_id)
        # No longer update session_id in users table; session-user link is managed in sessions table

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'status': 'success', 'message': 'Logged in with Discord'}
    )

@router.get("/link_discord", response_class=JSONResponse)
async def link_discord():
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={'status': 'error', 'message': 'Linking Discord to existing account not implemented yet'}
    )
