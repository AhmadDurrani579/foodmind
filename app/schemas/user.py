from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime


# -------------------------
# Create User (Signup)
# -------------------------
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    password: str


# -------------------------
# Login
# -------------------------
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# -------------------------
# Response Model
# -------------------------
class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    first_name: str
    last_name: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

    def with_base_url(self, base_url: str):
        if self.avatar_url:
            self.avatar_url = f"{base_url}{self.avatar_url}"
        return self
        

# -------------------------
# Token Response
# -------------------------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserMeResponse(BaseModel):
    success: bool
    user: UserResponse