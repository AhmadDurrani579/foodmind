from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    first_name: str
    avatar_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse