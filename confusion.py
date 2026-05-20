from ultralytics import YOLO

# Load your trained model
model = YOLO("best.pt")

metrics = model.val(data="C:/Users/DELL/Desktop/MajorProject/data_data/data.yaml")