from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MealType(str, Enum):
    breakfast = "breakfast"
    lunch     = "lunch"
    dinner    = "dinner"
    snack     = "snack"

class MealLogCreate(BaseModel):
    # required fields
    food_name_snapshot: str
    meal_type:  MealType
    calories:   float
    protein_g:  float
    carbs_g:    float
    fat_g:      float
    weight_g:   float
    # optional fields
    fiber_g:    Optional[float] = None
    confidence: Optional[float] = None
    depth_score: Optional[float] = None
    image_url:  Optional[str]  = None

class MealLogOut(BaseModel):
    id:         UUID4
    user_id:    UUID4
    food_name_snapshot: str
    meal_type:  str
    calories:   float
    protein_g:  float
    carbs_g:    float
    fat_g:      float
    fiber_g:    Optional[float]
    weight_g:   float
    image_url:  Optional[str]
    logged_at:  datetime

    class Config:
        from_attributes = True   # pydantic v2 (use orm_mode=True for v1)

class DailySummaryOut(BaseModel):
    date:           str
    total_calories: float
    total_protein:  float
    total_carbs:    float
    total_fat:      float
    meal_count:     int