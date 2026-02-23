import cv2
from vehicle_detector import VehicleDetector

def test_video_detection(video_path):
    """
    Test vehicle detection on a video file
    Press 'q' to quit, 'p' to pause/unpause
    """
    # Initialize detector
    print("Initializing detector...")
    detector = VehicleDetector()
    
    # Open video file
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        print("Make sure the file exists in your project folder!")
        return
    
    print("Processing video... Press 'q' to quit, 'p' to pause")
    
    paused = False
    frame_count = 0
    
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("Video ended!")
                break
            
            frame_count += 1
            
            # Process every 3rd frame for speed
            if frame_count % 3 == 0:
                # Detect vehicles
                detections = detector.detect_vehicles(frame)
                
                # Draw detections
                frame = detector.draw_detections(frame, detections)
                
                # Add info text
                cv2.putText(frame, f"Vehicles Detected: {len(detections)}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, "Press 'q' to quit, 'p' to pause", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Display frame
        cv2.imshow('Vehicle Detection Test', frame)
        
        # Handle keyboard input
        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            print("Quitting...")
            break
        elif key == ord('p'):
            paused = not paused
            print("Paused" if paused else "Resumed")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print(f"✓ Processed {frame_count} frames")

if __name__ == "__main__":
    # Test with your video file
    test_video_detection('test_video.mp4')