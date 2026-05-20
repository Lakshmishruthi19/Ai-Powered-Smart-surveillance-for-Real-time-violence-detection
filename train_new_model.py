from ultralytics import YOLO

# Load YOUR EXISTING trained model
print("Loading your current best model...")
model = YOLO('runs/detect/train2/weights/best.pt')

# Train on NEW violence_data dataset
print("Training on NEW violence_data dataset...")
results = model.train(
    data='violence_data/data.yaml',    # NEW dataset path
    epochs=100,                       # Train longer
    imgsz=640,                        # Image size
    batch=8,                          # Safe for laptop
    name='train3_new_violence_data'   # Save as train3
)

print("✅ NEW MODEL SAVED: runs/detect/train3_new_violence_data/weights/best.pt")