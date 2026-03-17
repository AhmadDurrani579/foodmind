from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    # Check if the email already exists in the database
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create the new user
    user = User(
        email=payload.email,
        username=payload.username,
        first_name=payload.first_name,
        password_hash=hash_password(payload.password)
    )

    # Save user to database
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create JWT token for the new user
    token = create_access_token({
        "user_id": str(user.id),
        "email": user.email
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password"
        )

    # Check password
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password"
        )

    # Generate JWT token after successful login
    token = create_access_token({
        "user_id": str(user.id),
        "email": user.email
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }