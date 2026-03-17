from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user

router = APIRouter()

@router.get("/users/me")
def get_me(user = Depends(get_current_user)):
    return user