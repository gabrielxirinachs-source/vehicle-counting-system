import cv2

def test_webcam():
    """
    Test if your webcam is working
    """
    print("Testing webcam...")
    print("Trying camera index 0...")
    
    cap = cv2.VideoCapture(0)  # 0 is usually the default webcam
    
    if not cap.isOpened():
        print("✗ Camera 0 not available")
        print("Try changing the number (0, 1, 2, etc.)")
        return
    
    print("✓ Camera connected!")
    print("Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Error reading frame")
            break
        
        # Add text overlay
        cv2.putText(frame, "Webcam Test - Press 'q' to quit", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Webcam Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("✓ Webcam test complete")

if __name__ == "__main__":
    test_webcam()