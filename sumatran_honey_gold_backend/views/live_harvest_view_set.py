import datetime
from django.utils import timezone
from googleapiclient.discovery import build
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from rest_framework.permissions import IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..services.youtube_client_service import YouTubeClient
from ..services.weather_service import WeatherService
from ..services.ffmpeg_service import FFmpegService
from ..middlewares.permissions import IsSuperUser
from ..serializers import LiveHarvestSerializer
from ..models import LiveHarvest

ffmpeg_service = FFmpegService()
weather_service = WeatherService()

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

            if LiveHarvest.objects.filter(status="LIVE").exists():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Masih ada live yang sedang berjalan",
                }, status=status.HTTP_400_BAD_REQUEST)

            youtube = YouTubeClient.get_client()
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

            weather = weather_service.get_weather(latitude, longitude)
            weather_temperature = weather["temperature"]
            weather_humidity = weather["humidity"]
            weather_wind_speed = weather["wind_speed"]

            data = {
                "youtube_video_id": broadcast["id"],
                "youtube_stream_id": stream["id"],
                "start_time": timezone.now(),
                "latitude": latitude,
                "longitude": longitude,
                "status": "LIVE",
                "weather_temperature": weather_temperature,
                "weather_humidity": weather_humidity,
                "weather_wind_speed": weather_wind_speed
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
            creds = Credentials.from_authorized_user_file("youtube_token.json")
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            youtube = build("youtube", "v3", credentials=creds)
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