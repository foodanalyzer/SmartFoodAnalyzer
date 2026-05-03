from ultralytics import YOLO
import numpy as np
import cv2

MODEL_PATH = "app/models/epoch8.pt" # put your .pt file here

_model = None

def load_model():
    global _model
    if _model is None:
        print("Loading YOLO model...")
        _model = YOLO(MODEL_PATH)
        print("YOLO loaded.")
    return _model

def detect_only(img_np: np.ndarray):
    """Fast detection, no segmentation. Returns top class, confidence, bbox."""
    model = load_model()
    results = model(img_np, conf=0.05, iou=0.7, verbose=False)
    boxes = results[0].boxes
    if len(boxes) == 0:
        return None
    class_names = results[0].names
    idx = int(np.argmax(boxes.conf.cpu().numpy()))
    cls = int(boxes.cls.cpu().numpy()[idx])
    conf = float(boxes.conf.cpu().numpy()[idx])
    bbox = boxes.xyxy.cpu().numpy()[idx].tolist()
    return {
        "detected_class": class_names[cls],
        "confidence": conf,
        "bbox": {"x": bbox[0], "y": bbox[1], "w": bbox[2]-bbox[0], "h": bbox[3]-bbox[1]}
    }

def segment(img_np: np.ndarray):
    """Full segmentation. Returns class, confidence, mask."""
    model = load_model()
    results = model(img_np, conf=0.05, iou=0.7, verbose=False)
    boxes = results[0].boxes
    if len(boxes) == 0 or results[0].masks is None:
        return None
    class_names = results[0].names
    idx = int(np.argmax(boxes.conf.cpu().numpy()))
    cls = int(boxes.cls.cpu().numpy()[idx])
    conf = float(boxes.conf.cpu().numpy()[idx])
    mask = results[0].masks.data.cpu().numpy()[idx]
    if mask.shape != img_np.shape[:2]:
        mask = cv2.resize(mask, (img_np.shape[1], img_np.shape[0]))
    return {
        "class_name": class_names[cls],
        "confidence": conf,
        "mask": mask
    }