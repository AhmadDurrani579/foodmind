from fastapi import APIRouter, Depends, Request
from app.core.dependencies import get_current_user
from app.schemas.user import UserResponse
from app.router.auth import build_user_response

router = APIRouter()

@router.get("/users/me", response_model=UserResponse)
def get_me(
    request: Request,
    user = Depends(get_current_user)
):
    return build_user_response(user, request)