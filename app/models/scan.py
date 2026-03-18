from sqlalchemy import Column, String, Integer, DECIMAL, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Scan(Base):

    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    dish_name = Column(String(200), nullable=False)
    cuisine = Column(String(100))

    calories = Column(Integer)
    protein_g = Column(DECIMAL(6,2))
    carbs_g = Column(DECIMAL(6,2))
    fat_g = Column(DECIMAL(6,2))
    fiber_g = Column(DECIMAL(6,2))

    health_score = Column(Integer)
    confidence = Column(Integer)
    validation_level = Column(String(20))
    final_confidence = Column(Integer)

    mobilenet_dish = Column(String(200))
    mobilenet_confidence = Column(DECIMAL(5,2))
    gemini_dish = Column(String(200))

    ingredients = Column(JSONB)
    recipe_steps = Column(JSONB)

    tags = Column(ARRAY(Text))
    allergens = Column(ARRAY(Text))

    cooking_tip = Column(Text)
    portion_size = Column(String(100))

    image_url = Column(Text)

    created_at = Column(TIMESTAMP, server_default=func.now())