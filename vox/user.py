from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import JSONResponse
from vox.limiter import limiter
from vox.database import get_user_preferences, update_user_preferences, get_all_vocal_data

router = APIRouter()


def get_db(request: Request):
    """Dependency to get db from app state."""
    return request.app.state.db


@router.post("/set_target_gender", response_class=JSONResponse)
@limiter.limit("50/hour")
async def set_target_gender(request: Request, db=Depends(get_db)):
    data = await request.json()
    target_gender = data.get("target", "unspecified").strip()

    await update_user_preferences(db, target_gender=target_gender)

    request.app.state.logger.info(f"set_target_gender: {target_gender}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "target_gender": target_gender}
    )


@router.post("/set_user_info", response_class=JSONResponse)
@limiter.limit("50/hour")
async def set_user_info(request: Request, db=Depends(get_db)):
    data = await request.json()
    user_name = data.get("name", "friend").strip()[:50]
    user_pronouns = data.get("pronouns", "they/them/theirs/themselves").strip()

    if not user_name:
        request.app.state.logger.error(f"set_user_info failed: Name cannot be empty")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Name cannot be empty"}
        )

    await update_user_preferences(db, user_name=user_name, user_pronouns=user_pronouns)

    request.app.state.logger.info(f"set_user_info: Name: {user_name}, Pronouns: {user_pronouns}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "success", "user_name": user_name, "pronouns": user_pronouns}
    )


@router.get("/get_performances", response_class=JSONResponse)
async def get_performances(request: Request, db=Depends(get_db)):
    vocal_data = await get_all_vocal_data(db)
    
    performances = [
        {
            "timestamp": row['timestamp'],
            "pitch": row['pitch'],
            "hnr": row['hnr'],
            "harmonics": row['harmonics'],
            "formants": row['formants'],
            "recording_path": row['recording_path']
        }
        for row in vocal_data
    ]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=performances
    )


@router.api_route("/profile", methods=["GET", "POST"], response_class=JSONResponse)
async def profile(request: Request, db=Depends(get_db)):
    if request.method == 'GET':
        user_prefs = await get_user_preferences(db)
        
        if not user_prefs:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'status': 'error', 'message': 'User preferences not found'}
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                'status': 'success',
                'user_name': user_prefs['user_name'],
                'user_pronouns': user_prefs['user_pronouns'],
                'target_gender': user_prefs['target_gender']
            }
        )
    else:
        data = await request.json()
        user_name = data.get('name')
        user_pronouns = data.get('pronouns')
        
        if not user_name and not user_pronouns:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'status': 'error', 'message': 'No updates provided'}
            )
        
        await update_user_preferences(db, user_name=user_name, user_pronouns=user_pronouns)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'status': 'success', 'message': 'Profile updated'}
        )
