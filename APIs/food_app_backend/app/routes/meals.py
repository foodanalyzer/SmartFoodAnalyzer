from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime

from app.database           import get_db
from app.utils.auth       import get_current_user   # reuse existing
from app.models.meal_logs     import MealLog
from app.schemas.meal      import MealLogCreate, MealLogOut, DailySummaryOut

router = APIRouter()


@router.post("/log", response_model=MealLogOut, status_code=201)
def log_meal(
    body: MealLogCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Save a meal after /food/analyze returns results."""
    meal = MealLog(
        **body.dict(),
        user_id=current_user.id   # taken from JWT, not from body
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


@router.get("/history", response_model=List[MealLogOut])
def get_meal_history(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all meals for the logged-in user, newest first."""
    meals = (
        db.query(MealLog)
        .filter(MealLog.user_id == current_user.id)
        .order_by(MealLog.logged_at.desc())
        .all()
    )
    return meals


@router.get("/daily-summary", response_model=DailySummaryOut)
def daily_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Return aggregated calorie + macro totals for today."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    meals = (
        db.query(MealLog)
        .filter(
            MealLog.user_id == current_user.id,
            MealLog.logged_at >= today_start
        )
        .all()
    )
    return {
        "date":           str(date.today()),
        "total_calories": round(sum(m.calories  for m in meals), 1),
        "total_protein":  round(sum(m.protein_g for m in meals), 1),
        "total_carbs":    round(sum(m.carbs_g   for m in meals), 1),
        "total_fat":      round(sum(m.fat_g     for m in meals), 1),
        "meal_count":     len(meals)
    }