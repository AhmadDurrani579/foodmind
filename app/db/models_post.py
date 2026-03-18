#
# models_post.py
# FoodMind Backend
#
# app/db/models_post.py
#

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base


class PostDB(Base):

    __tablename__ = "posts"

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
    scan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=True
    )

    # ── Content ───────────────────────
    caption     = Column(Text,        nullable=True)
    image_url   = Column(Text,        nullable=True)

    # ── Food Data (denormalised) ──────
    # Copied from scan for fast feed queries
    dish_name   = Column(String(200), nullable=True)
    cuisine     = Column(String(100), nullable=True)
    calories    = Column(Integer,     nullable=True)
    protein_g   = Column(Integer,     nullable=True)
    carbs_g     = Column(Integer,     nullable=True)
    fat_g       = Column(Integer,     nullable=True)
    health_score = Column(Integer,    nullable=True)
    tags        = Column(Text,        nullable=True)  # JSON string

    # ── Social ────────────────────────
    likes_count    = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)

    # ── Timestamp ─────────────────────
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    def __repr__(self):
        return f"<Post {self.dish_name} by user={self.user_id}>"