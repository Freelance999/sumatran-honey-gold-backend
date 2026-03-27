import json
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from rest_framework import status, viewsets
from googleapiclient.discovery import build
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from rest_framework.permissions import IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..services.encode_decode_service import EncodeDecodeService
from ..middlewares.permissions import IsSuperUser
from ..serializers import SettingSerializer
from ..models import Setting

class SettingViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["generate_channel_info", "youtube_callback"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["create_youtube_token", "fetch_settings"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"], url_path="fetch")
    def fetch_settings(self, request):
        try:
            settings = Setting.objects.all()
            serializer = SettingSerializer(settings, many=True)

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Settings Fetched Successfully",
                "data": serializer.data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["post"], url_path="youtube-token")
    def create_youtube_token(self, request):
        try:
            flow = Flow.from_client_secrets_file(
                "secret_youtube.json",
                scopes=["https://www.googleapis.com/auth/youtube"],
                redirect_uri=f"{settings.BASE_URL}/api/youtube/callback/"
            )

            state = EncodeDecodeService.encode_state({
                "user_id": request.user.id
            })

            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                state=state
            )

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Url for auth create successfully",
                "data": {
                    "authentication_url": auth_url,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["get"], url_path="youtube/callback")
    def youtube_callback(self, request):
        try:
            state_raw = request.GET.get("state")

            if not state_raw:
                return Response({
                    "message": "State is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            state_data = EncodeDecodeService.decode_state(state_raw)
            user_id = state_data.get("user_id")

            if not user_id:
                return Response({
                    "message": "Invalid state data"
                }, status=status.HTTP_400_BAD_REQUEST)

            flow = Flow.from_client_secrets_file(
                "secret_youtube.json",
                scopes=["https://www.googleapis.com/auth/youtube"],
                state=state_raw,
                redirect_uri=f"{settings.BASE_URL}/api/youtube/callback/"
            )

            flow.fetch_token(authorization_response=request.build_absolute_uri())
            creds = flow.credentials

            Setting.objects.update_or_create(
                key="youtube_token",
                defaults={
                    "value": json.dumps({
                        "user_id": user_id,
                        "token": creds.token,
                        "refresh_token": creds.refresh_token,
                        "token_uri": creds.token_uri,
                        "client_id": creds.client_id,
                        "client_secret": creds.client_secret,
                        "scopes": creds.scopes
                    })
                }
            )

            return Response({
                "status": status.HTTP_200_OK,
                "message": "YouTube connected successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["get"], url_path="channel-info")
    def get_channel_info(self, request):
        try:
            creds = Credentials.from_authorized_user_file("youtube_token.json")

            if creds.expired and creds.refresh_token:
                creds.refresh(Request())

            youtube = build("youtube", "v3", credentials=creds)

            response = youtube.channels().list(
                part="snippet,statistics,brandingSettings",
                mine=True
            ).execute()

            items = response.get("items", [])
            if not items:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Channel tidak ditemukan"
                }, status=status.HTTP_404_NOT_FOUND)

            channel = items[0]

            snippet = channel.get("snippet", {})
            statistics = channel.get("statistics", {})
            branding = channel.get("brandingSettings", {})
            custom_url = snippet.get("customUrl")
            channel_id = channel.get("id")

            if custom_url:
                channel_url = f"https://www.youtube.com/{custom_url}"
            else:
                channel_url = f"https://www.youtube.com/channel/{channel_id}"

            data = {
                "channel_id": channel_id,
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "custom_url": custom_url,
                "channel_url": channel_url,
                "published_at": snippet.get("publishedAt"),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "country": snippet.get("country"),
                "subscriber_count": statistics.get("subscriberCount"),
                "video_count": statistics.get("videoCount"),
                "view_count": statistics.get("viewCount"),
                "banner": branding.get("image", {}).get("bannerExternalUrl"),
            }

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Success get channel info",
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)