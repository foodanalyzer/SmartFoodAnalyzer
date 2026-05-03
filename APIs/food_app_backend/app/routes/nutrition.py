from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.nutrition_db import NutritionDB
from app.schemas.nutrition import FoodSearchResult, FoodDetailResponse
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/nutrition", tags=["Nutrition Database"])


# ── Helper mappers ────────────────────────────

def food_to_search_result(food: NutritionDB) -> FoodSearchResult:
    return FoodSearchResult(
        food_id           = food.id,
        name_en           = food.name_en,
        name_ur           = food.name_ur,
        category          = food.category.value if food.category else "other",
        density_g_cm3     = food.density_g_cm3,
        calories_per_100g = food.calories_per_100g,
        protein           = food.protein_per_100g,
        carbs             = food.carbs_per_100g,
        fat               = food.fat_per_100g,
        fiber             = food.fiber_per_100g,
    )


def food_to_detail(food: NutritionDB) -> FoodDetailResponse:
    return FoodDetailResponse(
        food_id           = food.id,
        name_en           = food.name_en,
        name_ur           = food.name_ur,
        category          = food.category.value if food.category else "other",
        density_g_cm3     = food.density_g_cm3,
        calories_per_100g = food.calories_per_100g,
        protein_g         = food.protein_per_100g,
        carbs_g           = food.carbs_per_100g,
        fat_g             = food.fat_per_100g,
        fiber_g           = food.fiber_per_100g,
        serving_size_g    = food.serving_size_g,
        yolo_class_name   = food.yolo_class_name,
        description       = food.description,
    )


# ── ENDPOINT 1: Search foods (for manual user search) ────────────────────────

@router.get(
    "/foods",
    response_model=List[FoodSearchResult],
    summary="Search Pakistani food database"
)
def search_foods(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    search_term = q.strip().lower()

    try:
        partial_matches = (
            db.query(NutritionDB)
            .filter(
                or_(
                    NutritionDB.name_en.ilike(f"%{search_term}%"),
                    NutritionDB.name_ur.ilike(f"%{search_term}%")
                )
            )
            .limit(limit)
            .all()
        )

        fuzzy_matches = (
            db.query(NutritionDB)
            .filter(func.similarity(NutritionDB.name_en, search_term) > 0.2)
            .order_by(func.similarity(NutritionDB.name_en, search_term).desc())
            .limit(limit)
            .all()
        )

        seen_ids = set()
        results = []
        for food in partial_matches + fuzzy_matches:
            if food.id not in seen_ids:
                seen_ids.add(food.id)
                results.append(food)

        return [food_to_search_result(f) for f in results[:limit]]

    except Exception:
        results = (
            db.query(NutritionDB)
            .filter(NutritionDB.name_en.ilike(f"%{search_term}%"))
            .limit(limit)
            .all()
        )
        return [food_to_search_result(f) for f in results]


# ── ENDPOINT 2: Get food by UUID (for results screen) ──────────────────────
@router.get(
    "/foods/{food_id}",
    response_model=FoodDetailResponse,
    summary="Get full nutrition detail for one food"
)
def get_food_by_id(
    food_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    food = db.query(NutritionDB).filter(NutritionDB.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail=f"Food '{food_id}' not found")
    return food_to_detail(food)


# ── ENDPOINT 3: THE KEY ONE — called by ML pipeline after YOLO detection ──────

@router.get(
    "/foods/by-class/{yolo_class_name}",
    response_model=FoodDetailResponse,
    summary="Get all nutrition data by YOLO class name — used by ML pipeline"
)
def get_food_by_yolo_class(
    yolo_class_name: str,
    db: Session = Depends(get_db),
):
    """
    THIS IS THE API YOUR ML PIPELINE CALLS AFTER YOLO DETECTS A FOOD.

    FULL FLOW:
    ──────────────────────────────────────────────────────────────────
    Step 1:  YOLOv8-seg detects food → outputs class name e.g. "biryani"
    Step 2:  Pipeline calls GET /nutrition/foods/by-class/biryani
    Step 3:  This API returns:
                {
                  food_id:           "uuid...",
                  name_en:           "Chicken Biryani",
                  name_ur:           "چکن بریانی",
                  category:          "rice",
                  density_g_cm3:     0.85,       ← used to compute weight
                  calories_per_100g: 195,
                  protein_g:         12.5,
                  carbs_g:           28.0,
                  fat_g:             4.5,
                  fiber_g:           0.8,
                  ...
                }
    Step 4:  Pipeline uses density_g_cm3:
                weight_g = volume_cm3 × density_g_cm3
    Step 5:  Pipeline scales all nutrients by weight:
                calories = (calories_per_100g / 100) × weight_g
                protein  = (protein_g / 100) × weight_g
                carbs    = (carbs_g / 100) × weight_g
                fat      = (fat_g / 100) × weight_g
                fiber    = (fiber_g / 100) × weight_g
    Step 6:  Final result displayed to user

    MATCHING STRATEGY (3 levels — most to least strict):
    ──────────────────────────────────────────────────────────────────
    Level 1: Exact match      "biryani" == "biryani"           ✅ best
    Level 2: Partial match    "chicken_biryani" contains "biryani" ✅ ok
    Level 3: Fuzzy match      "biyrani" ≈ "biryani" via pg_trgm  ✅ fallback
    """

    class_name = yolo_class_name.strip().lower()

    # ── Level 1: Exact match on yolo_class_name column ───────────────────────
    food = (
        db.query(NutritionDB)
        .filter(NutritionDB.yolo_class_name == class_name)
        .first()
    )
    if food:
        return food_to_detail(food)

    # ── Level 2: Partial match — yolo name contains a known class ─────────────
    # Handles cases like yolo outputs "chicken_biryani" but DB has "biryani"
    food = (
        db.query(NutritionDB)
        .filter(
            or_(
                NutritionDB.yolo_class_name.ilike(f"%{class_name}%"),
                func.position(NutritionDB.yolo_class_name.in_([class_name])),
                NutritionDB.name_en.ilike(f"%{class_name.replace('_', ' ')}%")
            )
        )
        .first()
    )
    if food:
        return food_to_detail(food)

    # ── Level 3: Fuzzy trigram match via pg_trgm ──────────────────────────────
    # Catches typos and close variations
    try:
        food = (
            db.query(NutritionDB)
            .filter(
                or_(
                    func.similarity(NutritionDB.yolo_class_name, class_name) > 0.3,
                    func.similarity(NutritionDB.name_en, class_name.replace("_", " ")) > 0.3
                )
            )
            .order_by(
                func.similarity(NutritionDB.yolo_class_name, class_name).desc()
            )
            .first()
        )
        if food:
            return food_to_detail(food)
    except Exception:
        pass  # pg_trgm not available, skip fuzzy

    # ── Nothing found ─────────────────────────────────────────────────────────
    raise HTTPException(
        status_code=404,
        detail=(
            f"No food found for YOLO class '{yolo_class_name}'. "
            f"Make sure this class name exists in the nutrition_db table "
            f"in the yolo_class_name column. "
            f"Your YOLO model classes must match what is stored in the database."
        )
    )
