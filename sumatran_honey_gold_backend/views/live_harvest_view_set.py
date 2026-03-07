import time
import datetime
import threading
import subprocess
from django.utils import timezone
from googleapiclient.discovery import build
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from google.oauth2.credentials import Credentials
from rest_framework.permissions import IsAuthenticated
from ..models import LiveHarvest
from ..services.ffmpeg_service import FFmpegService
from ..serializers import LiveHarvestSerializer
from ..middlewares.permissions import IsSuperUser
from ..middlewares.authentications import BearerTokenAuthentication

ffmpeg_service = FFmpegService()

class LiveHarvestViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["create", "stop_live"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in []:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
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

            stream_key = stream["cdn"]["ingestionInfo"]["streamName"]
            ingestion_address = stream["cdn"]["ingestionInfo"]["ingestionAddress"]
            youtube_rtmp = f"{ingestion_address}/{stream_key}"

            data = {
                "youtube_video_id": broadcast["id"],
                "youtube_stream_id": stream["id"],
                "start_time": timezone.now(),
                "latitude": latitude,
                "longitude": longitude,
                "status": "LIVE"
            }

            serializer = LiveHarvestSerializer(data=data)
            if serializer.is_valid():
                live = serializer.save()
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            ffmpeg_service.start_streaming(youtube_rtmp)

            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Live started on youtube!",
                "data": {
                    "youtube_stream_id": live.youtube_stream_id,
                    "youtube_video_id": live.youtube_video_id,
                    "youtube_rtmp": youtube_rtmp
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["post"], url_path="stop-live")
    def stop_live(self, request, pk=None):
        try:
            id = request.data.get("id")

            live = LiveHarvest.objects.get(youtube_stream_id=id)
            ffmpeg_service.stop_streaming()
            creds = Credentials.from_authorized_user_file("youtube_token.json")
            youtube = build("youtube", "v3", credentials=creds)

            youtube.liveBroadcasts().transition(
                broadcastStatus="complete",
                id=live.youtube_video_id,
                part="status"
            ).execute()

            live.status = "STOPPED"
            live.end_time = timezone.now()
            live.save()

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Live stopped successfully",
            }, status=status.HTTP_200_OK)

        except LiveHarvest.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Live harvest not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)