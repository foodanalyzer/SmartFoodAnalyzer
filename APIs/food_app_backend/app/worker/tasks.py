from app.worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.analysis_tasks import AnalysisTask
from app.services import yolo_util, nutrition_calc
from app.services.midas_util import load_model
from PIL import Image
from io import BytesIO
import numpy as np
import torch
from datetime import datetime

midas, transform, device = load_model()

def get_depth_map(img_np):
    input_batch = transform(img_np).to(device)
    with torch.no_grad():
        pred = midas(input_batch)
        pred = torch.nn.functional.interpolate(
            pred.unsqueeze(1), size=img_np.shape[:2],
            mode="bicubic", align_corners=False
        ).squeeze()
    depth = pred.cpu().numpy()
    depth_norm = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    table_depth = np.percentile(depth_norm, 95)
    return (depth_norm / (table_depth + 1e-8)) * 30.0  # 30cm camera height

@celery_app.task(bind=True)
def run_food_analysis(self, task_id: str, image_bytes: bytes, bbox_coords: dict, camera_height_cm: float):
    db = SessionLocal()
    try:
        # Update status to processing
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        task.status = "processing"
        db.commit()

        # Load image
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(img)

        # Step 1: MiDaS depth
        depth_map = get_depth_map(img_np)

        # Step 2: YOLOv8 segmentation
        seg = yolo_util.segment(img_np)
        if seg is None:
            task.status = "failed"
            task.error_msg = "No food detected"
            task.completed_at = datetime.utcnow()
            db.commit()
            return

        # Step 3: Nutrition calculation
        result = nutrition_calc.calculate_nutrition(seg["mask"], depth_map, seg["class_name"], db)
        if result is None:
            task.status = "failed"
            task.error_msg = f"Food '{seg['class_name']}' not in nutrition DB"
            task.completed_at = datetime.utcnow()
            db.commit()
            return

        result["confidence"] = seg["confidence"]
        result["mask_image_url"] = None  # optionally save mask image to disk/S3

        task.status = "done"
        task.result_json = result
        task.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if task:
            task.status = "failed"
            task.error_msg = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()