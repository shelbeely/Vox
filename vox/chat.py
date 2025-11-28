from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from vox.user import get_session_id
from vox.limiter import limiter
from fastapi import status

router = APIRouter()


def get_db_pool(request: Request):
    """Dependency to get db_pool from app state."""
    return request.app.state.db_pool


@router.post("/", response_class=JSONResponse)
@limiter.limit("50/hour")
async def chat(request: Request, sid: str = Depends(get_session_id), db_pool=Depends(get_db_pool)):
    try:
        data = await request.json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Empty message"}
            )

        async with db_pool.acquire() as conn:
            # Look up user via sessions table
            session_row = await conn.fetchrow("SELECT user_id FROM sessions WHERE session_id = $1", sid)
            user = None
            if session_row and session_row["user_id"]:
                user = await conn.fetchrow(
                    "SELECT user_name, user_pronouns FROM users WHERE user_id = $1",
                    session_row["user_id"]
                )
        user_name = user['user_name'] if user and user['user_name'] else 'friend'
        user_pronouns = user['user_pronouns'] if user and user['user_pronouns'] else 'they/them/theirs/themselves'

        from vox.utils import LLM_PERSONALITY_PROMPT_BASE
        from vox.llm import chat_with_llm

        system_prompt = LLM_PERSONALITY_PROMPT_BASE + f"\nUser info:\nName: {user_name}\nPronouns: {user_pronouns}\n"
        reply = await chat_with_llm(system_prompt, user_message)

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

from fastapi import Query
from vox.database import fetch_chat_history_async

@router.get("/history", response_class=JSONResponse)
async def chat_history(request: Request, limit: int = Query(50), db_pool=Depends(get_db_pool)):
    """
    Fetch the most recent chat messages for the current session.
    """
    session = request.session
    sid = session.get('id', 'default')
    try:
        messages = await fetch_chat_history_async(db_pool, sid, limit)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "messages": messages}
        )
    except Exception as e:
        request.app.state.logger.error(f"Chat history error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Failed to fetch chat history"}
        )
