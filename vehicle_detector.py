import cv2
from ultralytics import YOLO
import numpy as np

class VehicleDetector:
    """
    AI-powered vehicle detector using YOLO
    This class handles detecting vehicles in images/video frames
    """
    
    def __init__(self):
        print("Loading AI model (this might take a minute first time)...")
        
        # Load YOLO model - will auto-download on first run
        self.model = YOLO('yolov8n.pt')
        
        # Vehicle class IDs from COCO dataset:
        # 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
        self.vehicle_classes = [2, 3, 5, 7]
        
        print("✓ Detector ready!")
    
    def detect_vehicles(self, frame):
        """
        Detect vehicles in a single frame
        
        Args:
            frame: OpenCV image (BGR format)
            
        Returns:
            List of detections with bounding boxes and confidence
        """
        # Run YOLO detection on the frame
        results = self.model(frame, verbose=False)
        
        detections = []
        
        # Process each detection
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Get the class ID and confidence score
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Only keep vehicles with good confidence
                if class_id in self.vehicle_classes and confidence > 0.5:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    detections.append({
                        'bbox': (int(x1), int(y1), int(x2), int(y2)),
                        'confidence': confidence,
                        'class_id': class_id,
                        'class_name': self.get_class_name(class_id)
                    })
        
        return detections
    
    def get_class_name(self, class_id):
        """Convert class ID to human-readable name"""
        names = {2: 'Car', 3: 'Motorcycle', 5: 'Bus', 7: 'Truck'}
        return names.get(class_id, 'Vehicle')
    
    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes and labels on the frame
        
        Args:
            frame: OpenCV image
            detections: List of detections from detect_vehicles()
            
        Returns:
            Frame with drawn boxes
        """
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            name = det['class_name']
            
            # Draw green rectangle around vehicle
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Create label with vehicle type and confidence
            label = f"{name} {conf:.2f}"
            
            # Draw black background for text
            (text_width, text_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )
            cv2.rectangle(frame, (x1, y1 - text_height - 10), 
                         (x1 + text_width, y1), (0, 255, 0), -1)
            
            # Draw white text
            cv2.putText(frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame

# Test the detector
if __name__ == "__main__":
    print("Testing Vehicle Detector...")
    detector = VehicleDetector()
    print("✓ Detector initialized successfully!")
    print("\nYou can now use this detector in other scripts.")