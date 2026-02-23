import cv2
from vehicle_counter import VehicleCounter
import subprocess
import json

def get_youtube_stream_url(youtube_url):
    """
    Get the direct video stream URL from a YouTube video
    """
    try:
        cmd = [
            'yt-dlp',
            '-f', 'best',
            '-g',  # Get direct URL
            youtube_url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting stream URL: {e}")
        return None

def test_youtube_traffic_cam(youtube_url):
    """
    Test with a YouTube live traffic camera
    """
    print("Getting stream URL from YouTube...")
    stream_url = get_youtube_stream_url(youtube_url)
    
    if not stream_url:
        print("✗ Could not get stream URL")
        return
    
    print(f"✓ Got stream URL!")
    print("\nStarting vehicle counter...")
    
    counter = VehicleCounter(line_position=0.5)
    cap = cv2.VideoCapture(stream_url)
    
    if not cap.isOpened():
        print("✗ Could not open stream")
        return
    
    print("✓ Stream opened!")
    print("\nPress 'q' to quit\n")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream ended")
            break
        
        frame_count += 1
        
        # Process every 2nd frame for better performance
        if frame_count % 2 == 0:
            frame = counter.process_frame(frame)
        
        cv2.imshow('YouTube Traffic Stream', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"\nTotal vehicles counted: {counter.total_count}")

if __name__ == "__main__":
    # Popular live traffic cameras on YouTube
    # Find more at: youtube.com/results?search_query=live+traffic+camera
    
    test_urls = [
        "https://www.youtube.com/watch?v=1EiC9bvVGnk",  # Example traffic cam
    ]
    
    print("="*60)
    print("YOUTUBE LIVE TRAFFIC CAMERA TEST")
    print("="*60)
    
    # You can paste any YouTube live traffic stream URL here
    youtube_url = input("\nPaste YouTube live traffic camera URL\n(or press Enter for default): ")
    
    if not youtube_url:
        youtube_url = test_urls[0]
        print(f"Using default: {youtube_url}")
    
    test_youtube_traffic_cam(youtube_url)