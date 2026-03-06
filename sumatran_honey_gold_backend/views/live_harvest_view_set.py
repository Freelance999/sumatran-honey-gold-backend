import time
import datetime
import threading
import subprocess
from googleapiclient.discovery import build
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from google.oauth2.credentials import Credentials
from rest_framework.permissions import IsAuthenticated
from ..middlewares.permissions import IsSuperUser
from ..middlewares.authentications import BearerTokenAuthentication
from ..serializers import LiveHarvestSerializer
from ..models import LiveHarvest

class LiveHarvestViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def create(self, request):
        try:
            latitude = request.data.get("latitude")
            longitude = request.data.get("longitude")

            creds = Credentials.from_authorized_user_file("youtube_token.json")
            youtube = build("youtube", "v3", credentials=creds)
            start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

            broadcast = youtube.liveBroadcasts().insert(
                part="snippet,status,contentDetails",
                body={
                    "snippet": {
                        "title": "Live Panen Madu",
                        "scheduledStartTime": start_time
                    },
                    "status": {
                        "privacyStatus": "unlisted"
                    },
                    "contentDetails": {
                        "enableAutoStart": True,
                        "enableAutoStop": True
                    }
                }
            ).execute()

            stream = youtube.liveStreams().insert(
                part="snippet,cdn",
                body={
                    "snippet": {"title": "Honey Stream"},
                    "cdn": {
                        "resolution": "720p",
                        "frameRate": "30fps",
                        "ingestionType": "rtmp"
                    }
                }
            ).execute()

            youtube.liveBroadcasts().bind(
                part="id,contentDetails",
                id=broadcast["id"],
                streamId=stream["id"]
            ).execute()

            # live = LiveHarvest.objects.create(
            #     youtube_video_id=broadcast["id"],
            #     start_time=start_time,
            #     latitude=latitude,
            #     longitude=longitude,
            #     status="LIVE"
            # )

            stream_key = stream["cdn"]["ingestionInfo"]["streamName"]
            ingestion_address = stream["cdn"]["ingestionInfo"]["ingestionAddress"]
            youtube_rtmp = f"{ingestion_address}/{stream_key}"

            start_ffmpeg_worker(youtube_rtmp)

            return Response({
                "status": 201,
                "message": "Live created",
                "data": {
                    "video_id": broadcast["id"],
                    "youtube_rtmp": youtube_rtmp
                }
            })

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def start_ffmpeg_worker(youtube_rtmp):
    def worker():
        while True:
            try:
                cmd = [
                    "ffmpeg",
                    "-i", "rtmp://localhost:1935/liveHarvest",
                    "-f", "lavfi",
                    "-i", "anullsrc",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    "-f", "flv",
                    youtube_rtmp
                ]

                process = subprocess.Popen(cmd)
                process.wait()

            except Exception as e:
                print("FFmpeg error:", e)

            print("Retrying ffmpeg in 3 seconds...")
            time.sleep(3)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()