from ultralytics import YOLO
import cv2

# Load your trained model
model = YOLO("best.pt")  # replace with your weights file

# Open the video
video_path = "demo_video.mp4"
cap = cv2.VideoCapture(video_path)

# Get video properties
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps    = int(cap.get(cv2.CAP_PROP_FPS))

# Output video file
out = cv2.VideoWriter('output_demo.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Run detection
    results = model.predict(frame, verbose=False)  # verbose=False avoids too much print

    # YOLOv8 returns a list of results; we can draw boxes
    annotated_frame = results[0].plot()  # draws boxes on frame
    
    # Show the frame
    cv2.imshow("YOLOv8 Detection", annotated_frame)
    
    # Write to output video
    out.write(annotated_frame)

    # Press 'q' to stop early
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()
print("Video processed and saved as output_demo.mp4")