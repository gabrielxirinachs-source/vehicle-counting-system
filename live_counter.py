import cv2
from vehicle_counter import VehicleCounter
import datetime
import json
import os

class LiveVehicleCounter:
    """
    Main application for live vehicle counting
    """
    
    def __init__(self, camera_source=0, save_logs=True):
        print("Initializing Live Vehicle Counter...")
        
        self.counter = VehicleCounter(line_position=0.5)
        self.camera_source = camera_source
        self.save_logs = save_logs
        
        # Create logs folder if it doesn't exist
        if save_logs and not os.path.exists('logs'):
            os.makedirs('logs')
            print("✓ Created logs folder")
        
        print("✓ Live counter ready!")
    
    def save_count_log(self):
        """Save current count to daily log file"""
        if not self.save_logs:
            return
        
        data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'total_count': self.counter.total_count,
            'session_duration_minutes': int((datetime.datetime.now().timestamp() - 
                                            self.counter.session_start) / 60)
        }
        
        # Log filename based on today's date
        log_file = f"logs/count_{datetime.date.today()}.json"
        
        # Load existing logs or create new list
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(data)
        
        # Save updated logs
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        print(f"✓ Count saved to {log_file}")
    
    def run(self):
        """
        Run the live counting system
        """
        print("\n" + "="*50)
        print("PORTMIAMI LIVE VEHICLE COUNTER")
        print("="*50)
        
        # Open camera
        cap = cv2.VideoCapture(self.camera_source)
        
        if not cap.isOpened():
            print("✗ Error: Could not open camera")
            print(f"Camera source: {self.camera_source}")
            print("\nTroubleshooting:")
            print("1. Make sure your camera is connected")
            print("2. Try different camera indices (0, 1, 2)")
            print("3. Check if another program is using the camera")
            return
        
        print("✓ Camera connected successfully!")
        print("\nControls:")
        print("  'q' - Quit and save")
        print("  's' - Save count now")
        print("  'r' - Reset counter")
        print("  'p' - Pause/Resume")
        print("\n" + "="*50 + "\n")
        
        paused = False
        
        try:
            while True:
                if not paused:
                    ret, frame = cap.read()
                    
                    if not ret:
                        print("✗ Error reading frame from camera")
                        break
                    
                    # Process frame with counter
                    frame = self.counter.process_frame(frame)
                    
                    # Add timestamp
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, timestamp, 
                               (10, frame.shape[0] - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    
                    # Add status
                    cv2.putText(frame, "LIVE", 
                               (frame.shape[1] - 80, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                # Display frame
                cv2.imshow('PortMiami Vehicle Counter - LIVE', frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\nQuitting...")
                    break
                elif key == ord('s'):
                    self.save_count_log()
                elif key == ord('r'):
                    print("\nResetting counter...")
                    self.counter = VehicleCounter(line_position=0.5)
                elif key == ord('p'):
                    paused = not paused
                    print("PAUSED" if paused else "RESUMED")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        
        finally:
            # Cleanup
            cap.release()
            cv2.destroyAllWindows()
            
            # Save final count
            self.save_count_log()
            
            print("\n" + "="*50)
            print("SESSION SUMMARY")
            print("="*50)
            print(f"Total Vehicles Counted: {self.counter.total_count}")
            print(f"Session Duration: {int((datetime.datetime.now().timestamp() - self.counter.session_start) / 60)} minutes")
            print("="*50)
            print("\n✓ Session ended successfully!")

if __name__ == "__main__":
    # Configuration
    CAMERA_INDEX = 0  # Change this if your camera is on a different index
    
    # Create and run the app
    app = LiveVehicleCounter(camera_source=CAMERA_INDEX)
    app.run()