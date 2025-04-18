from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
import openai
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_base = os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
openai.api_key = os.environ.get("OPENROUTER_API_KEY")

from vox.limiter import limiter
from fastapi import status

router = APIRouter()

# Dependency to get db_pool from app state
def get_db_pool(request: Request):
    return request.app.state.db_pool

@router.post("/", response_class=JSONResponse)
@limiter.limit("50/hour")
async def chat(request: Request, db_pool=Depends(get_db_pool)):
    try:
        data = await request.json()
        user_message = data.get("message", "").strip()
        session = request.session
        sid = session.get('id', 'default')

        if not user_message:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Empty message"}
            )

        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT user_name, user_pronouns FROM users WHERE session_id = $1",
                sid
            )
        user_name = user['user_name'] if user and user['user_name'] else 'friend'
        user_pronouns = user['user_pronouns'] if user and user['user_pronouns'] else 'they/them/theirs/themselves'

        from vox.utils import LLM_PERSONALITY_PROMPT_BASE

        system_prompt = LLM_PERSONALITY_PROMPT_BASE + f"\nUser info:\nName: {user_name}\nPronouns: {user_pronouns}\n"

        def do_request():
            response = openai.chat.completions.create(
                model="google/gemini-2.0-flash-001",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            return response

        response_data = await asyncio.to_thread(do_request)

        # openai>=1.0.0 returns an object, not a dict
        choices = getattr(response_data, "choices", [])
        if not choices:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"status": "error", "message": "No response from LLM"}
            )

        reply = choices[0].message.content.strip()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "message": reply}
        )

    except Exception as e:
        request.app.state.logger.error(f"Chat error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Failed to get response from LLM"}
        )
