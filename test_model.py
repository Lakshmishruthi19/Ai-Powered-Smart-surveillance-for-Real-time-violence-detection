from ultralytics import YOLO
import cv2

# Load model
model = YOLO("best.pt")   # <-- put correct path

# Open test video
cap = cv2.VideoCapture("fight_test.mp4")  # or 0 for webcam

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)
    annotated = results[0].plot()

    cv2.imshow("Detection Test", annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()