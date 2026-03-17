from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
import os, uuid

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from fastapi import Request


router = APIRouter(prefix="/auth", tags=["Authentication"])

os.makedirs("uploads", exist_ok=True)


@router.post("/signup", response_model=TokenResponse)
def signup(payload: UserCreate, request: Request, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        username=payload.username,
        first_name=payload.first_name,
        last_name=payload.last_name,
        password_hash=hash_password(payload.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({
        "id": str(user.id),
        "email": user.email
    })

    # Build full avatar URL
    avatar_url = None
    if user.avatar_url:
        avatar_url = f"{request.base_url}{user.avatar_url.lstrip('/')}"

    user_response = UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=avatar_url,
        created_at=user.created_at
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_response
    }

@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password"
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password"
        )

    token = create_access_token({
        "id": str(user.id),
        "email": user.email
    })

    avatar_url = None
    if user.avatar_url:
        avatar_url = f"{request.base_url}{user.avatar_url.lstrip('/')}"

    user_response = UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=avatar_url,
        created_at=user.created_at
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_response
    }

@router.post("/users/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    os.makedirs("uploads", exist_ok=True)

    file_ext = file.filename.split(".")[-1]
    filename = f"{user.id}_{uuid.uuid4()}.{file_ext}"

    file_path = f"uploads/{filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    user.avatar_url = f"/uploads/{filename}"
    db.commit()

    return {"avatar_url": user.avatar_url}