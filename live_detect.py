from ultralytics import YOLO
import cv2

model = YOLO("runs/detect/train2/weights/best.pt")
cap = cv2.VideoCapture(0)

print("🔴 LIVE VIOLENCE DETECTION - Press Q to quit")
while True:
    ret, frame = cap.read()
    if not ret: break
    
    results = model(frame)
    annotated = results[0].plot()
    
    # ALERT if violence detected
    for box in results[0].boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        if conf > 0.5:  # Confidence threshold
            cv2.putText(annotated, "🚨 VIOLENCE ALERT!", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            print("🚨 VIOLENCE DETECTED!")
    
    cv2.imshow("Violence Detection LIVE", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()