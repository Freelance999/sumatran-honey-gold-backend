import time
import subprocess
import threading

class FFmpegService:
    def __init__(self):
        self.ffmpeg_running = False
        self.ffmpeg_process = None
        self.ffmpeg_thread = None
    
    def start_streaming(self, youtube_rtmp):
        self.ffmpeg_running = True
        
        def worker():
            while self.ffmpeg_running:
                try:
                    cmd = [
                        "ffmpeg",
                        "-i", "rtsp://localhost:8554/liveHarvest",
                        # "-f", "lavfi",
                        # "-i", "anullsrc",
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-ar", "44100",
                        "-b:a", "128k",
                        "-map", "0:v:0",
                        "-map", "0:a:0?",
                        # "-shortest",
                        "-f", "flv",
                        youtube_rtmp
                    ]

                    self.ffmpeg_process = subprocess.Popen(cmd)
                    self.ffmpeg_process.wait()

                except Exception as e:
                    print(f"FFmpeg error: {e}")

                if self.ffmpeg_running:
                    print("Retrying ffmpeg in 3 seconds...")
                    time.sleep(3)
        
        self.ffmpeg_thread = threading.Thread(target=worker, daemon=True)
        self.ffmpeg_thread.start()
    
    def stop_streaming(self):
        self.ffmpeg_running = False
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()