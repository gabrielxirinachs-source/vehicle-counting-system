"""
Flask Web Dashboard for Vehicle Counting System
Run this file to start the web server
"""

from flask import Flask, render_template, Response, jsonify
import cv2
from vehicle_counter import VehicleCounter
import json
import datetime
from threading import Thread, Lock
import time

app = Flask(__name__)

# Global variables
counter = None
camera = None
output_frame = None
lock = Lock()
is_running = False
stats = {
    'total_count': 0,
    'hourly_rate': 0,
    'session_start': None,
    'last_detection': None,
    'status': 'Stopped'
}

def initialize_camera(camera_source=0):
    """Initialize the camera and start processing"""
    global counter, camera, is_running, stats
    
    print("Initializing camera...")
    counter = VehicleCounter(line_position=0.5)
    camera = cv2.VideoCapture(camera_source)
    
    if not camera.isOpened():
        print("Error: Could not open camera")
        return False
    
    is_running = True
    stats['session_start'] = datetime.datetime.now().isoformat()
    stats['status'] = 'Running'
    print("✓ Camera initialized successfully!")
    return True

def process_camera():
    """Process camera frames continuously"""
    global output_frame, camera, counter, is_running, stats
    
    frame_count = 0
    
    while is_running:
        if camera is None or not camera.isOpened():
            time.sleep(1)
            continue
        
        ret, frame = camera.read()
        if not ret:
            print("Error reading frame")
            time.sleep(1)
            continue
        
        frame_count += 1
        
        # Process every 2nd frame for performance
        if frame_count % 2 == 0:
            # Count vehicles
            frame = counter.process_frame(frame)
            
            # Update stats
            with lock:
                stats['total_count'] = counter.total_count
                stats['last_detection'] = datetime.datetime.now().isoformat()
                
                # Calculate hourly rate
                if counter.session_start:
                    elapsed_hours = (time.time() - counter.session_start) / 3600
                    if elapsed_hours > 0:
                        stats['hourly_rate'] = int(counter.total_count / elapsed_hours)
            
            # Update output frame
            with lock:
                output_frame = frame.copy()

def generate_frames():
    """Generate frames for video streaming"""
    global output_frame, lock
    
    while True:
        with lock:
            if output_frame is None:
                continue
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', output_frame)
            if not ret:
                continue
            
            frame = buffer.tobytes()
        
        # Yield frame in byte format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        time.sleep(0.033)  # ~30 FPS

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stats')
def get_stats():
    """Get current statistics"""
    with lock:
        return jsonify(stats)

@app.route('/api/start/<int:camera_id>')
def start_camera(camera_id):
    """Start the camera"""
    global is_running
    
    if is_running:
        return jsonify({'status': 'error', 'message': 'Already running'})
    
    if initialize_camera(camera_id):
        # Start processing thread
        thread = Thread(target=process_camera, daemon=True)
        thread.start()
        return jsonify({'status': 'success', 'message': 'Camera started'})
    else:
        return jsonify({'status': 'error', 'message': 'Could not start camera'})

@app.route('/api/stop')
def stop_camera():
    """Stop the camera"""
    global is_running, camera, stats
    
    is_running = False
    stats['status'] = 'Stopped'
    
    if camera is not None:
        camera.release()
        camera = None
    
    return jsonify({'status': 'success', 'message': 'Camera stopped'})

@app.route('/api/reset')
def reset_counter():
    """Reset the counter"""
    global counter, stats
    
    if counter is not None:
        counter = VehicleCounter(line_position=0.5)
        stats['total_count'] = 0
        stats['hourly_rate'] = 0
        stats['session_start'] = datetime.datetime.now().isoformat()
    
    return jsonify({'status': 'success', 'message': 'Counter reset'})

@app.route('/api/history')
def get_history():
    """Get historical data from database"""
    try:
        from database import VehicleDatabase
        db = VehicleDatabase()
        
        # Get last 7 days
        data = db.get_last_n_days(7)
        
        history = []
        for day in data:
            date = day['date']
            count = day['count']
            
            # Get peak hour for this date
            peak = db.get_peak_hour(date)
            
            history.append({
                'date': date,
                'total': count,
                'peak_hour': f"{peak['hour']:02d}:00" if peak else '00:00',
                'peak_count': peak['count'] if peak else 0
            })
        
        return jsonify(history)
        
    except Exception as e:
        print(f"Database error: {e}")
        # Return mock data as fallback
        today = datetime.date.today()
        history = []
        
        for i in range(7):
            date = today - datetime.timedelta(days=i)
            history.append({
                'date': date.isoformat(),
                'total': 0,
                'peak_hour': '00:00',
                'peak_count': 0
            })
        
        return jsonify(history)

if __name__ == '__main__':
    print("="*60)
    print("VEHICLE COUNTING SYSTEM - WEB DASHBOARD")
    print("="*60)
    print("\nStarting Flask server...")
    print("Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)