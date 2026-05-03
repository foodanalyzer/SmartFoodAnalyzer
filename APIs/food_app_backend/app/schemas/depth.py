from pydantic import BaseModel
from typing import Optional

class BBox(BaseModel):
    x: int
    y: int
    w: int
    h: int

class DepthValidateResponse(BaseModel):
    status: str          # "valid" | "too_near" | "too_far"
    depth_score: float
    color: str           # "green" | "red"
    message: str