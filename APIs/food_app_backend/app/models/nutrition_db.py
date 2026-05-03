from sqlalchemy import Column, String, Float, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class FoodCategoryEnum(str, enum.Enum):
    rice        = "rice"
    bread       = "bread"
    curry       = "curry"
    meat        = "meat"
    lentils     = "lentils"
    vegetables  = "vegetables"
    dairy       = "dairy"
    snacks      = "snacks"
    sweets      = "sweets"
    beverages   = "beverages"
    salad       = "salad"
    soup        = "soup"
    other       = "other"


class NutritionDB(Base):
    """
    Your Pakistani food dataset CSV imported into PostgreSQL.
    Each row = one food item with density and per-100g macros.

    KEY FIELDS:
    - density_g_cm3     → used by volume estimator to get weight
    - yolo_class_name   → must EXACTLY match the class label your YOLOv8 model outputs
                          so the pipeline can auto-lookup nutrition after detection
    """
    __tablename__ = "nutrition_db"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name_en  = Column(String(150), nullable=False, index=True)   # e.g. "Chicken Biryani"
    name_ur  = Column(String(150), nullable=True)                # e.g. "چکن بریانی"

    category = Column(Enum(FoodCategoryEnum), nullable=False, default=FoodCategoryEnum.other)

    # CRITICAL for your pipeline — volume × density = weight in grams
    density_g_cm3 = Column(Float, nullable=False)

    # All macros stored per 100g — scaled proportionally at runtime
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g  = Column(Float, nullable=False, default=0)
    carbs_per_100g    = Column(Float, nullable=False, default=0)
    fat_per_100g      = Column(Float, nullable=False, default=0)
    fiber_per_100g    = Column(Float, nullable=False, default=0)

    # Typical serving size in grams (optional, shown in UI)
    serving_size_g = Column(Float, nullable=True)

    # Must match YOLOv8 class label EXACTLY — e.g. "biryani", "roti", "nihari"
    # This is the bridge between ML output and your nutrition data
    yolo_class_name = Column(String(100), nullable=True, unique=True, index=True)

    description = Column(Text, nullable=True)

    # Relationship — lets you do food.meal_logs in Python
    meal_logs = relationship("MealLog", back_populates="food")
