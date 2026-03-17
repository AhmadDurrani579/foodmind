from fastapi import APIRouter, Depends, Request
from app.core.dependencies import get_current_user
from app.schemas.user import UserResponse, UserMeResponse
from app.router.auth import build_user_response

router = APIRouter()

@router.get("/users/me", response_model=UserMeResponse)
def get_me(request: Request, user=Depends(get_current_user)):

    user_data = build_user_response(user, request)

    return {
        "success": True,
        "user": user_data
    }