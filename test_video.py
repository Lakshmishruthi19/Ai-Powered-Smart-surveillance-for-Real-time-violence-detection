import cv2
from ultralytics import YOLO

# Load model
model = YOLO("best.pt")

# Load video
cap = cv2.VideoCapture("demo_video.mp4")

# Get original video width & height
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Create VideoWriter OUTSIDE loop ✅
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output_demo_video.mp4', fourcc, 20.0, (width, height))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)
    annotated_frame = results[0].plot()

    # WRITE FRAME ✅
    out.write(annotated_frame)

    # Show video
    cv2.imshow("Demo Test", annotated_frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
out.release()
cv2.destroyAllWindows()
