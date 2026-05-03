import torch
import cv2
import numpy as np

MODEL_PATH = "app/models/dpt_hybrid_384.pt"

def load_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load architecture WITHOUT downloading
    midas = torch.hub.load("intel-isl/MiDaS", "DPT_Hybrid", pretrained=False)

    # Load weights from local file
    midas.load_state_dict(torch.load(MODEL_PATH, map_location=device))

    midas.to(device)
    midas.eval()

    # Load transforms (still uses cache, lightweight)
    midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
    transform = midas_transforms.dpt_transform

    return midas, transform, device