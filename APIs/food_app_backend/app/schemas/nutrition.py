from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from enum import Enum


class FoodCategoryEnum(str, Enum):
    rice       = "rice"
    bread      = "bread"
    curry      = "curry"
    meat       = "meat"
    lentils    = "lentils"
    vegetables = "vegetables"
    dairy      = "dairy"
    snacks     = "snacks"
    sweets     = "sweets"
    beverages  = "beverages"
    salad      = "salad"
    soup       = "soup"
    other      = "other"


# ── Response for search list (/nutrition/foods?q=...) ─────────────────────────
# Lighter response — only fields needed to show in a search results list

class FoodSearchResult(BaseModel):
    """
    Returned as a list item in the search results.
    Kept lean — only what the search screen needs to display.
    """
    food_id           : UUID
    name_en           : str
    name_ur           : Optional[str]
    category          : str
    density_g_cm3     : float
    calories_per_100g : float
    protein           : float   # protein_per_100g
    carbs             : float   # carbs_per_100g
    fat               : float   # fat_per_100g
    fiber             : float   # fiber_per_100g

    model_config = {"from_attributes": True}


# ── Response for detail view (/nutrition/foods/{id}) ──────────────────────────
# Full response — everything stored about this food

class FoodDetailResponse(BaseModel):
    """
    Returned for a single food item.
    Used on Results screen and Food Detail view.
    Also used internally by the ML pipeline to fetch density.
    """
    food_id           : UUID
    name_en           : str
    name_ur           : Optional[str]
    category          : str
    density_g_cm3     : float
    calories_per_100g : float
    protein_g         : float
    carbs_g           : float
    fat_g             : float
    fiber_g           : float
    serving_size_g    : Optional[float]
    yolo_class_name   : Optional[str]
    description       : Optional[str]

    model_config = {"from_attributes": True}