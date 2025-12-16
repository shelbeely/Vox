from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from vox.limiter import limiter
from fastapi import status

router = APIRouter()


def get_db(request: Request):
    """Dependency to get db from app state."""
    return request.app.state.db


@router.post("/", response_class=JSONResponse)
@limiter.limit("50/hour")
async def chat(request: Request, db=Depends(get_db)):
    try:
        data = await request.json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Empty message"}
            )

        # Get user preferences
        from vox.database import get_user_preferences
        user_prefs = await get_user_preferences(db)
        user_name = user_prefs['user_name'] if user_prefs else 'friend'
        user_pronouns = user_prefs['user_pronouns'] if user_prefs else 'they/them/theirs/themselves'

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
async def chat_history(request: Request, limit: int = Query(50), db=Depends(get_db)):
    """
    Fetch the most recent chat messages.
    """
    try:
        messages = await fetch_chat_history_async(db, limit)
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
