from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class TaskStatusEnum(str, enum.Enum):
    pending    = "pending"
    processing = "processing"
    done       = "done"
    failed     = "failed"


class AnalysisTask(Base):
    """
    Tracks each async food analysis job submitted via POST /food/analyze.

    WHY THIS EXISTS:
    The ML pipeline (MiDaS + YOLOv8 + volume estimation) takes 5-15 seconds.
    Instead of making the mobile app wait with an open HTTP connection, we:
      1. Accept the image → create a task row → return task_id immediately (202)
      2. Run the ML pipeline in the background (Celery worker)
      3. Store results in result_json when done
      4. Mobile app polls GET /food/result/{task_id} every 2 seconds
      5. When status = "done", result_json has all the nutrition data

    result_json example when done:
    {
        "food_name": "Chicken Biryani",
        "confidence": 0.94,
        "weight_g": 312.5,
        "calories": 487.3,
        "protein_g": 28.1,
        "carbs_g": 52.4,
        "fat_g": 16.8,
        "fiber_g": 2.1,
        "mask_image_url": "/media/masks/abc123.png",
        "food_id": "uuid-of-food-in-nutrition-db",
        "estimated_volume_cm3": 245.0,
        "depth_score": 0.73
    }
    """
    __tablename__ = "analysis_tasks"

    # task_id is the Celery task UUID — string, not UUID type
    task_id = Column(String(64), primary_key=True)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    status = Column(
        Enum(TaskStatusEnum),
        nullable=False,
        default=TaskStatusEnum.pending,
        index=True
    )

    # JSONB = PostgreSQL's native JSON with indexing support
    # Stores the full pipeline output — flexible, no schema needed
    result_json = Column(JSONB, nullable=True)

    # Set when status = "failed"
    error_msg = Column(Text, nullable=True)

    # Input metadata stored for debugging
    image_path      = Column(Text, nullable=True)     # path to uploaded image
    bbox_x          = Column(String(20), nullable=True)
    bbox_y          = Column(String(20), nullable=True)
    bbox_w          = Column(String(20), nullable=True)
    bbox_h          = Column(String(20), nullable=True)
    camera_height_cm = Column(String(20), nullable=True)

    created_at   = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    user = relationship("User", back_populates="analysis_tasks")
