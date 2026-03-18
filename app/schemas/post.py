#
# schemas/post.py
# FoodMind Backend
#

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class PostCreate(BaseModel):
    scan_id:    Optional[UUID] = None
    caption:    Optional[str]  = None
    image_url:  Optional[str]  = None

    # Food data from scan
    dish_name:   Optional[str] = None
    cuisine:     Optional[str] = None
    calories:    Optional[int] = None
    protein_g:   Optional[int] = None
    carbs_g:     Optional[int] = None
    fat_g:       Optional[int] = None
    health_score: Optional[int] = None
    tags:        Optional[str] = None  # JSON string


class PostResponse(BaseModel):
    id:            UUID
    user_id:       UUID
    scan_id:       Optional[UUID]  = None
    caption:       Optional[str]   = None
    image_url:     Optional[str]   = None

    dish_name:     Optional[str]   = None
    cuisine:       Optional[str]   = None
    calories:      Optional[int]   = None
    protein_g:     Optional[int]   = None
    carbs_g:       Optional[int]   = None
    fat_g:         Optional[int]   = None
    health_score:  Optional[int]   = None
    tags:          Optional[str]   = None

    likes_count:    int = 0
    comments_count: int = 0
    created_at:     datetime

    # User info (joined)
    username:   Optional[str] = None
    first_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True