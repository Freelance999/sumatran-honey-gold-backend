import time
import subprocess
import threading

class FFmpegService:
    RTSP_INPUT_URL = "rtsp://localhost:8554/liveHarvest"

    def __init__(self):
        self.ffmpeg_running = False
        self.ffmpeg_process = None
        self.ffmpeg_thread = None

    def wait_until_input_ready(self, timeout_seconds=30):
        deadline = time.time() + timeout_seconds

        while self.ffmpeg_running and time.time() < deadline:
            probe_cmd = [
                "ffprobe",
                "-v", "error",
                "-rtsp_transport", "tcp",
                "-show_entries", "stream=codec_type",
                "-of", "default=noprint_wrappers=1",
                self.RTSP_INPUT_URL,
            ]
            result = subprocess.run(
                probe_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                return True

            print("Waiting for MediaMTX publisher on liveHarvest...")
            time.sleep(1)

        return False
    
    def start_streaming(self, youtube_rtmp):
        self.ffmpeg_running = True
        
        def worker():
            while self.ffmpeg_running:
                try:
                    if not self.wait_until_input_ready():
                        if self.ffmpeg_running:
                            print("MediaMTX publisher is not ready yet")
                        continue

                    cmd = [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel", "info",
                        "-fflags", "+genpts",
                        "-rtsp_transport", "tcp",
                        "-i", self.RTSP_INPUT_URL,
                        "-map", "0:v:0",
                        "-map", "0:a:0?",
                        "-c:v", "libx264",
                        "-preset", "veryfast",
                        "-tune", "zerolatency",
                        "-pix_fmt", "yuv420p",
                        "-profile:v", "main",
                        "-b:v", "2500k",
                        "-maxrate", "2500k",
                        "-bufsize", "5000k",
                        "-g", "60",
                        "-c:a", "aac",
                        "-ar", "44100",
                        "-ac", "2",
                        "-b:a", "128k",
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
