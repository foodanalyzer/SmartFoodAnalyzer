from pydantic import BaseModel
from typing import Optional

class FoodAnalyzeResponse(BaseModel):
    task_id: str

class FoodResultResponse(BaseModel):
    status: str   # "processing" | "done" | "failed"
    food_name: Optional[str] = None
    confidence: Optional[float] = None
    weight_g: Optional[float] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    mask_image_url: Optional[str] = None
    food_id: Optional[str] = None

class DetectOnlyResponse(BaseModel):
    detected_class: str
    confidence: float
    bbox: dict