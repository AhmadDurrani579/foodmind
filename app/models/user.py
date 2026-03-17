from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False
    )

    first_name = Column(
        String(100),
        nullable=False
    )

    password_hash = Column(
        Text,
        nullable=False
    )

    avatar_url = Column(Text)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )