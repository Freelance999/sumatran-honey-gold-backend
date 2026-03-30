import json
import secrets
from django.conf import settings
from django.core.cache import cache
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
        if self.action in ["generate_channel_info", "youtube_callback", "get_channel_info"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["create_youtube_token", "fetch_settings"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]

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
                redirect_uri=f"{settings.BASE_URL}/api/sumatran-honey-gold/v1/setting/youtube/callback/"
            )

            state_token = secrets.token_urlsafe(32)

            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
                state=state_token,
            )

            cache.set(f"youtube_oauth_state:{state_token}", {
                "user_id": request.user.id,
                "code_verifier": flow.code_verifier,
            }, timeout=600)

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
            state_token = request.GET.get("state")

            if not state_token:
                return Response({
                    "message": "State is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            state_data = cache.get(f"youtube_oauth_state:{state_token}")

            if not state_data:
                return Response({
                    "message": "State expired or invalid"
                }, status=status.HTTP_400_BAD_REQUEST)

            user_id = state_data.get("user_id")
            code_verifier = state_data.get("code_verifier")

            if not user_id:
                return Response({
                    "message": "Invalid state data"
                }, status=status.HTTP_400_BAD_REQUEST)

            flow = Flow.from_client_secrets_file(
                "secret_youtube.json",
                scopes=["https://www.googleapis.com/auth/youtube"],
                state=state_token,
                redirect_uri=f"{settings.BASE_URL}/api/sumatran-honey-gold/v1/setting/youtube/callback/"
            )

            if code_verifier:
                flow.code_verifier = code_verifier

            flow.fetch_token(authorization_response=request.build_absolute_uri())
            creds = flow.credentials
            cache.delete(f"youtube_oauth_state:{state_token}")

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
                        "scopes": list(creds.scopes) if creds.scopes else [],
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

            is_live_enabled = False

            try:
                live_response = youtube.liveBroadcasts().list(
                    part="status",
                    broadcastType="all",
                    mine=True,
                    maxResults=1
                ).execute()
                print("Live response", live_response)
                is_live_enabled = True

            except Exception:
                is_live_enabled = False

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
                "is_live_streaming_enabled": is_live_enabled,
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