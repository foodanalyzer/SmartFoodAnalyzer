import numpy as np
from sqlalchemy.orm import Session
from app.models.nutrition_db import NutritionDB

BOX_WIDTH_PX = 315
BOX_HEIGHT_PX = 504
REAL_WIDTH_CM = 5.0
REAL_HEIGHT_CM = 8.0
CAMERA_HEIGHT_CM = 30.0
CM_PER_PX_W = REAL_WIDTH_CM / BOX_WIDTH_PX
CM_PER_PX_H = REAL_HEIGHT_CM / BOX_HEIGHT_PX
AREA_FACTOR = CM_PER_PX_W * CM_PER_PX_H

def calculate_nutrition(mask: np.ndarray, depth_map: np.ndarray, class_name: str, db: Session):
    food = db.query(NutritionDB).filter(
        NutritionDB.yolo_class_name == class_name.strip().lower()
    ).first()
    if not food:
        return None

    binary = (mask > 0.5).astype(np.uint8)
    area_px = np.sum(binary)
    area_cm2 = area_px * AREA_FACTOR

    depth_vals = depth_map[binary == 1]
    if len(depth_vals) == 0:
        return None

    mean_depth = np.mean(depth_vals)
    height_cm = max(0, min(CAMERA_HEIGHT_CM - mean_depth, CAMERA_HEIGHT_CM))
    volume_cm3 = area_cm2 * height_cm
    weight_g = volume_cm3 * food.density_g_cm3
    f = weight_g / 100

    return {
        "food_id": str(food.id),
        "food_name": food.name_en,
        "weight_g": round(weight_g, 2),
        "calories": round(food.calories_per_100g * f, 2),
        "protein_g": round(food.protein_per_100g * f, 2),
        "carbs_g": round(food.carbs_per_100g * f, 2),
        "fat_g": round(food.fat_per_100g * f, 2),
        "fiber_g": round(food.fiber_per_100g * f, 2),
    }