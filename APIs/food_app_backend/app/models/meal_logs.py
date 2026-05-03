from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class MealTypeEnum(str, enum.Enum):
    breakfast = "breakfast"
    lunch     = "lunch"
    dinner    = "dinner"
    snack     = "snack"


class MealLog(Base):
    """
    Every meal a user scans and saves is stored here.
    Many-to-one with both users and nutrition_db.

    DESIGN DECISIONS:
    - food_name_snapshot: we store the food name AT LOG TIME so history
      stays correct even if nutrition_db is updated later
    - calories/macros stored as snapshot for the same reason
    - confidence: YOLOv8 detection confidence score (0.0 to 1.0)
    - mask_image_url: path/URL to the segmentation mask image
    """
    __tablename__ = "meal_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK → users.id
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # FK → nutrition_db.id  (nullable — in case food not found in DB)
    food_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nutrition_db.id", ondelete="SET NULL"),
        nullable=True
    )

    # Snapshot fields — copied from nutrition_db at log time
    # Never join back to nutrition_db for these — use snapshot values
    food_name_snapshot = Column(String(150), nullable=False)
    weight_g           = Column(Float, nullable=False)
    calories           = Column(Float, nullable=False)
    protein_g          = Column(Float, nullable=False, default=0)
    carbs_g            = Column(Float, nullable=False, default=0)
    fat_g              = Column(Float, nullable=False, default=0)
    fiber_g            = Column(Float, nullable=False, default=0)

    meal_type = Column(
        Enum(MealTypeEnum),
        nullable=False,
        default=MealTypeEnum.snack
    )

    # Image paths — store relative path or S3 URL
    image_url      = Column(Text, nullable=True)   # original photo
    mask_image_url = Column(Text, nullable=True)   # YOLOv8 segmentation mask overlay

    # ML output metadata
    confidence = Column(Float, nullable=True)      # YOLOv8 confidence 0.0–1.0

    # Depth estimation metadata (useful for debugging/research)
    estimated_volume_cm3 = Column(Float, nullable=True)
    depth_score          = Column(Float, nullable=True)

    notes = Column(Text, nullable=True)            # optional user note

    # logged_at is indexed — used heavily in date-range queries for history
    logged_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

    # Relationships
    user = relationship("User", back_populates="meal_logs")
    food = relationship("NutritionDB", back_populates="meal_logs")
