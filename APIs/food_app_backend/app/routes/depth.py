from fastapi import APIRouter, File, UploadFile, Form
from PIL import Image
import numpy as np
from io import BytesIO
import torch
from app.services.midas_util import load_model

router = APIRouter(prefix="/depth", tags=["Depth"])

midas, transform, device = load_model()

DEPTH_TOO_NEAR = 0.75   # tune from your testing
DEPTH_TOO_FAR  = 0.25

@router.post("/validate")
async def validate_depth(
    file: UploadFile = File(...),
    x: int = Form(315), y: int = Form(505),
    w: int = Form(5), h: int = Form(8)
):
    img_bytes = await file.read()
    img = Image.open(BytesIO(img_bytes)).convert("RGB")
    img_np = np.array(img)

    input_batch = transform(img_np).to(device)
    with torch.no_grad():
        pred = midas(input_batch)
        pred = torch.nn.functional.interpolate(
            pred.unsqueeze(1), size=img_np.shape[:2],
            mode="bicubic", align_corners=False
        ).squeeze()

    depth_map = pred.cpu().numpy()
    depth_norm = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min() + 1e-8)

    # Crop to bbox region
    roi = depth_norm[y:y+h, x:x+w]
    score = float(np.mean(roi)) if roi.size > 0 else float(depth_norm[depth_norm.shape[0]//2, depth_norm.shape[1]//2])

    if score > DEPTH_TOO_NEAR:
        return {"status": "too_near", "depth_score": score, "color": "red", "message": "Too close! Move camera back."}
    elif score < DEPTH_TOO_FAR:
        return {"status": "too_far", "depth_score": score, "color": "red", "message": "Too far! Move camera closer."}
    else:
        return {"status": "valid", "depth_score": score, "color": "green", "message": "Perfect distance!"}