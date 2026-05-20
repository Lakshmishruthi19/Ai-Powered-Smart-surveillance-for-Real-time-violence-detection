from ultralytics import YOLO
import os

if _name_ == '_main_':
    # 1. Load the model
    model = YOLO('yolov8n.pt') 

    # 2. Train the model
    # Note: 'workers=0' is often needed on Windows to prevent errors
    model.train(
        data='data.yaml', 
        epochs=100, 
        imgsz=640, 
        device=0,      # Change to 'cpu' if you don't have an NVIDIA GPU
        workers=0      
    )