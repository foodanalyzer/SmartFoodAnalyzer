from sqlalchemy import Column, Float, String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class DietTypeEnum(str, enum.Enum):
    none = "none"
    vegetarian = "vegetarian"
    low_carb = "low_carb"
    high_protein = "high_protein"
    low_fat = "low_fat"


class UserGoals(Base):
    """
    One-to-one with users table.
    Stores daily calorie and macro targets for each user.
    Auto-created with defaults when a user registers.
    """
    __tablename__ = "user_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK → users.id  |  unique=True enforces one-to-one
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    daily_calorie_goal = Column(Float, nullable=False, default=2000)
    protein_goal_g     = Column(Float, nullable=False, default=50)
    carbs_goal_g       = Column(Float, nullable=False, default=250)
    fat_goal_g         = Column(Float, nullable=False, default=65)
    fiber_goal_g       = Column(Float, nullable=False, default=25)

    diet_type = Column(
        Enum(DietTypeEnum),
        nullable=False,
        default=DietTypeEnum.none
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationship — lets you do user.goals in Python
    user = relationship("User", back_populates="goals")
