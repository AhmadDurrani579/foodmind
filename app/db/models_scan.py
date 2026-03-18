#
# models_scan.py
# FoodMind Backend
#
# app/db/models_scan.py
#

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer,
    Float, Text, DateTime,
    ForeignKey, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.database import Base


class ScanDB(Base):

    __tablename__ = "scans"

    # ── Identity ──────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # ── Food Info ─────────────────────
    dish_name = Column(String(200), nullable=False)
    cuisine   = Column(String(100), nullable=True)

    # ── Nutrition ─────────────────────
    calories  = Column(Integer,  nullable=True)
    protein_g = Column(Float,    nullable=True)
    carbs_g   = Column(Float,    nullable=True)
    fat_g     = Column(Float,    nullable=True)
    fiber_g   = Column(Float,    nullable=True)

    # ── Scores ────────────────────────
    health_score      = Column(Integer,     nullable=True)
    confidence        = Column(Integer,     nullable=True)
    validation_level  = Column(String(20),  nullable=True)
    final_confidence  = Column(Integer,     nullable=True)

    # ── AI Sources ────────────────────
    mobilenet_dish        = Column(String(200), nullable=True)
    mobilenet_confidence  = Column(Float,       nullable=True)
    gemini_dish           = Column(String(200), nullable=True)

    # ── Detailed Data (JSONB) ─────────
    ingredients  = Column(JSONB, nullable=True)  # List[dict]
    recipe_steps = Column(JSONB, nullable=True)  # List[dict]

    # ── Arrays ────────────────────────
    tags      = Column(ARRAY(Text), nullable=True)
    allergens = Column(ARRAY(Text), nullable=True)

    # ── Text ──────────────────────────
    cooking_tip  = Column(Text,         nullable=True)
    portion_size = Column(String(100),  nullable=True)
    image_url    = Column(Text,         nullable=True)

    # ── Timestamp ─────────────────────
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    def __repr__(self):
        return (
            f"<Scan {self.dish_name} "
            f"({self.calories} kcal) "
            f"user={self.user_id}>"
        )