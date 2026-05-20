from ultralytics import YOLO

# Load the trained model (downloaded from Colab)
model = YOLO("best.pt")   # Make sure this file is in your project folder

# Run detection on video
results = model.predict(
    source="fight_video.mp4",  # Your test video
    show=True,                 # Show live output
    save=True,                 # Save output video
    conf=0.25                  # Confidence threshold (adjust if needed)
)

print("Detection completed successfully!")