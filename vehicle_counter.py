import cv2
from vehicle_detector import VehicleDetector
import time
import datetime

class VehicleCounter:
    """
    Counts vehicles crossing a virtual line in the video
    Now with database integration!
    """
    
    def __init__(self, line_position=0.5, use_database=True):
        self.detector = VehicleDetector()
        
        # Line position (0.0 = top, 1.0 = bottom)
        self.line_position = line_position
        
        # Tracking variables
        self.vehicle_centers = {}  # Track vehicle positions
        self.counted_ids = set()   # IDs that have been counted
        self.total_count = 0       # Total vehicles counted
        self.session_start = time.time()
        
        # Database integration
        self.use_database = use_database
        self.db = None
        self.session_id = None
        
        if use_database:
            try:
                from database import VehicleDatabase
                self.db = VehicleDatabase()
                # Create unique session ID
                self.session_id = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                self.db.create_session(self.session_id)
                print("✓ Database connected and session created")
            except ImportError:
                print("⚠ Database module not found - running without database")
                self.use_database = False
            except Exception as e:
                print(f"⚠ Database error: {e} - running without database")
                self.use_database = False
        
    def get_center(self, bbox):
        """Calculate center point of bounding box"""
        x1, y1, x2, y2 = bbox
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        return (center_x, center_y)
    
    def find_matching_vehicle(self, center, max_distance=50):
        """
        Find if this detection matches a previously tracked vehicle
        Returns vehicle ID if found, None if new vehicle
        """
        cx, cy = center
        
        for vid, (old_cx, old_cy) in self.vehicle_centers.items():
            distance = ((cx - old_cx)**2 + (cy - old_cy)**2)**0.5
            if distance < max_distance:
                return vid
        
        return None
    
    def determine_lane(self, center_x, frame_width):
        """
        Determine which lane the vehicle is in based on x position
        
        Args:
            center_x: X coordinate of vehicle center
            frame_width: Width of the frame
            
        Returns:
            Lane name (e.g., 'Lane 1', 'Lane 2', etc.)
        """
        # Divide frame into 4 equal lanes
        lane_width = frame_width / 4
        lane_number = int(center_x / lane_width) + 1
        return f'Lane {lane_number}'
    
    def process_frame(self, frame):
        """
        Process frame and count vehicles crossing the line
        """
        height, width = frame.shape[:2]
        line_y = int(height * self.line_position)
        
        # Detect vehicles in this frame
        detections = self.detector.detect_vehicles(frame)
        
        # Update tracking
        current_centers = {}
        
        for det in detections:
            center = self.get_center(det['bbox'])
            cx, cy = center
            
            # Only process vehicles near the counting line
            if abs(cy - line_y) < 50:
                # Check if this is a known vehicle
                vid = self.find_matching_vehicle(center)
                
                if vid is None:
                    # New vehicle detected near line
                    vid = len(self.vehicle_centers) + len(current_centers)
                    
                    # Count it if not already counted
                    if vid not in self.counted_ids:
                        self.total_count += 1
                        self.counted_ids.add(vid)
                        
                        # Determine lane
                        lane = self.determine_lane(cx, width)
                        
                        # Save to database
                        if self.use_database and self.db:
                            try:
                                self.db.add_vehicle(
                                    lane=lane,
                                    vehicle_type=det['class_name'],
                                    confidence=det['confidence'],
                                    session_id=self.session_id
                                )
                            except Exception as e:
                                print(f"Database error: {e}")
                        
                        timestamp = time.strftime('%H:%M:%S')
                        print(f"✓ Vehicle #{self.total_count} counted - {det['class_name']} in {lane} at {timestamp}")
                
                current_centers[vid] = center
        
        # Update tracked vehicles
        self.vehicle_centers = current_centers
        
        # Draw everything on frame
        frame = self.draw_interface(frame, detections, line_y)
        
        return frame
    
    def draw_interface(self, frame, detections, line_y):
        """Draw all visual elements on the frame"""
        height, width = frame.shape[:2]
        
        # Draw counting line (red)
        cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 3)
        cv2.putText(frame, "COUNTING LINE", (10, line_y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Draw lane dividers (dashed lines)
        lane_width = width / 4
        for i in range(1, 4):
            x = int(lane_width * i)
            for y in range(0, height, 20):
                cv2.line(frame, (x, y), (x, y + 10), (100, 100, 100), 1)
        
        # Draw vehicle detections (green boxes)
        frame = self.detector.draw_detections(frame, detections)
        
        # Draw statistics panel
        self.draw_stats_panel(frame)
        
        return frame
    
    def draw_stats_panel(self, frame):
        """Draw statistics overlay"""
        height, width = frame.shape[:2]
        
        # Semi-transparent black panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 140), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Total count (large)
        cv2.putText(frame, f"Total Count: {self.total_count}", 
                   (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        
        # Calculate hourly rate
        elapsed_hours = (time.time() - self.session_start) / 3600
        hourly_rate = int(self.total_count / elapsed_hours) if elapsed_hours > 0 else 0
        
        cv2.putText(frame, f"Hourly Rate: {hourly_rate} vehicles/hr", 
                   (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Current time
        current_time = time.strftime("%H:%M:%S")
        cv2.putText(frame, f"Time: {current_time}", 
                   (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # Database status
        if self.use_database:
            cv2.putText(frame, "DB: Connected", 
                       (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            cv2.putText(frame, "DB: Offline", 
                       (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    def end_session(self):
        """
        End the current session and save to database
        """
        if self.use_database and self.db and self.session_id:
            try:
                self.db.end_session(self.session_id, self.total_count)
                print(f"✓ Session {self.session_id} ended - {self.total_count} vehicles counted")
            except Exception as e:
                print(f"Error ending session: {e}")
    
    def get_today_stats(self):
        """
        Get today's statistics from database
        
        Returns:
            Dictionary with today's stats or None if database unavailable
        """
        if self.use_database and self.db:
            try:
                return self.db.generate_daily_report()
            except Exception as e:
                print(f"Error getting stats: {e}")
                return None
        return None

# Test the counter
if __name__ == "__main__":
    counter = VehicleCounter(line_position=0.6, use_database=True)
    cap = cv2.VideoCapture('test_video.mp4')
    
    print("Starting vehicle counter... Press 'q' to quit")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = counter.process_frame(frame)
            cv2.imshow('Vehicle Counter', frame)
            
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        counter.end_session()
        
        print(f"\n✓ Session complete!")
        print(f"Total vehicles counted: {counter.total_count}")
        
        # Show today's stats
        if counter.use_database:
            stats = counter.get_today_stats()
            if stats:
                print(f"\nToday's Statistics:")
                print(f"  Total: {stats['total_count']}")
                print(f"  Peak Hour: {stats['peak_hour']}")
                print(f"  Avg/Hour: {stats['avg_per_hour']}")