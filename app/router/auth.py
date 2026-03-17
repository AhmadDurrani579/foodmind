from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
import os, uuid

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token


router = APIRouter(prefix="/auth", tags=["Authentication"])

os.makedirs("uploads", exist_ok=True)


@router.post("/signup", response_model=TokenResponse)
def signup(payload: UserCreate, db: Session = Depends(get_db)):

    # Check email
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Check username
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

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

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):

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

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/users/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import uuid

    file_ext = file.filename.split(".")[-1]
    filename = f"{user.id}_{uuid.uuid4()}.{file_ext}"

    file_path = f"uploads/{filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # FULL PUBLIC URL
    avatar_url = f"https://ahmaddurrani-food-mind.hf.space/uploads/{filename}"

    user.avatar_url = avatar_url
    db.commit()

    return {
        "avatar_url": avatar_url
    }