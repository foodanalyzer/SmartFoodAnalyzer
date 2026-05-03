from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.analysis_tasks import AnalysisTask
from app.worker.tasks import run_food_analysis
from app.services import yolo_util
from PIL import Image
from io import BytesIO
import numpy as np
import uuid, base64
from app.utils.auth import get_current_user
from app.models.user import User
router = APIRouter(prefix="/food", tags=["Food"])

@router.post("/analyze")
async def analyze_food(
    file: UploadFile = File(...),
    bbox_x: int = Form(315),
    bbox_y: int = Form(505),
    bbox_w: int = Form(5),
    bbox_h: int = Form(8),
    camera_height_cm: float = Form(30.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")
    task_id = str(uuid.uuid4())

    # Save task to DB
    task = AnalysisTask(
    task_id=task_id,
    user_id=current_user.id,   # ✅ FIXED
    status="pending"
    )
    db.add(task)
    db.commit()

    # Queue Celery task
    run_food_analysis.apply_async(
        args=[task_id, image_bytes, {"x": bbox_x, "y": bbox_y, "w": bbox_w, "h": bbox_h}, camera_height_cm],
        task_id=task_id
    )

    return {"task_id": task_id}


@router.get("/result/{task_id}")
async def get_result(task_id: str, db: Session = Depends(get_db)):
    task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status in ("pending", "processing"):
        return {"status": "processing"}

    if task.status == "failed":
        return {"status": "failed", "error": task.error_msg}

    return {"status": "done", **task.result_json}


@router.post("/detect-only")
async def detect_only(file: UploadFile = File(...)):
    image_bytes = await file.read()
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img_np = np.array(img)

    result = yolo_util.detect_only(img_np)
    if result is None:
        raise HTTPException(status_code=404, detail="No food detected")

    return result