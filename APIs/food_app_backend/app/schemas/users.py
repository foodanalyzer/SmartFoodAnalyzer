from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

# ── Goals schemas ────────────────────────────────

class GoalsOut(BaseModel):
    user_id:              UUID4
    
    daily_calorie_goal: float
    protein_goal_g: float
    carbs_goal_g: float
    fat_goal_g: float
    fiber_goal_g: float

    class Config:
        from_attributes = True

class GoalsUpdate(BaseModel):
    # all fields optional — user can update just one if they want
    daily_calorie_goal: Optional[float] = None
    protein_goal_g: Optional[float] = None
    carbs_goal_g: Optional[float] = None
    fat_goal_g: Optional[float] = None
    fiber_goal_g: Optional[float] = None

# ── Profile schema ───────────────────────────────

class UserProfileOut(BaseModel):
    id:         UUID4
    name:       str
    email:      str
    gender:     Optional[str]
    date_of_birth: Optional[str]
    height_cm:  Optional[float]
    weight_kg:  Optional[float]
    disease:    Optional[str]
    created_at: Optional[datetime]
    goals:      Optional[GoalsOut]    # nested goals inside profile response

    class Config:
        from_attributes = True