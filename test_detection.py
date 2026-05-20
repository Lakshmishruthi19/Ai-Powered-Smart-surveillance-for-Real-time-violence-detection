from ultralytics import YOLO
import os

# Check if model exists
model_path = "runs/detect/train2/weights/best.pt"
if not os.path.exists(model_path):
    print(f"❌ Model not found: {model_path}")
    print("Available models:")
    os.system('dir runs\\detect\\train2\\weights')
    exit()

print("✅ Loading violence detection model...")
model = YOLO(model_path)

print("✅ Testing test_image.jpg...")
results = model("test_image.jpg")

print("✅ Results saved! Opening image...")
results[0].show()  # Opens image with red boxes

print("🎉 VIOLENCE DETECTION SUCCESS!")
print("Check: runs/detect/predict*/test_image.jpg")