from pydantic import BaseModel
from typing import Optional, List, Any
import uuid
from datetime import datetime


class ScanCreate(BaseModel):

    # ── Food Info ─────────────────────
    dish_name:    str
    cuisine:      Optional[str] = None

    # ── Nutrition ─────────────────────
    calories:     Optional[int]   = None
    protein_g:    Optional[float] = None
    carbs_g:      Optional[float] = None
    fat_g:        Optional[float] = None
    fiber_g:      Optional[float] = None

    # ── Scores ────────────────────────
    health_score:      Optional[int] = None
    confidence:        Optional[int] = None  # ← Gemini confidence
    validation_level:  Optional[str] = None  # ← high/medium/low
    final_confidence:  Optional[int] = None  # ← combined confidence

    # ── AI Sources ────────────────────
    mobilenet_dish:        Optional[str]   = None
    mobilenet_confidence:  Optional[float] = None
    gemini_dish:           Optional[str]   = None

    # ── Detailed Data ─────────────────
    ingredients:  Optional[List[dict]] = None  # ← dict not str
    recipe_steps: Optional[List[dict]] = None  # ← dict not str
    tags:         Optional[List[str]]  = None
    allergens:    Optional[List[str]]  = None
    cooking_tip:  Optional[str]        = None
    portion_size: Optional[str]        = None

    # ── Image ─────────────────────────
    image_url:    Optional[str]        = None


class ScanResponse(BaseModel):

    id:         uuid.UUID
    user_id:    uuid.UUID

    # ── Food Info ─────────────────────
    dish_name:    str
    cuisine:      Optional[str] = None

    # ── Nutrition ─────────────────────
    calories:     Optional[int]   = None
    protein_g:    Optional[float] = None
    carbs_g:      Optional[float] = None
    fat_g:        Optional[float] = None
    fiber_g:      Optional[float] = None

    # ── Scores ────────────────────────
    health_score:     Optional[int] = None
    confidence:       Optional[int] = None
    validation_level: Optional[str] = None
    final_confidence: Optional[int] = None

    # ── Detailed Data ─────────────────
    ingredients:  Optional[List[dict]] = None
    recipe_steps: Optional[List[dict]] = None
    tags:         Optional[List[str]]  = None
    allergens:    Optional[List[str]]  = None
    cooking_tip:  Optional[str]        = None
    portion_size: Optional[str]        = None
    image_url:    Optional[str]        = None

    created_at:   datetime

    class Config:
        from_attributes = True
