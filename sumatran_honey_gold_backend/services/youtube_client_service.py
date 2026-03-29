import os
import json
from googleapiclient.discovery import build
from rest_framework.response import Response
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from ..models import Setting

TOKEN_FILE = "youtube_token.json"

class YouTubeClient:

    @staticmethod
    def save_to_db(creds, user_id=None):
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

    @staticmethod
    def get_client():
        creds = None

        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE)
        else:
            setting = Setting.objects.filter(key="youtube_token").first()

            if not setting:
                return Response({
                    "message": "Token not found"
                }, status=404)

            token_data = json.loads(setting.value)

            creds = Credentials(
                token=token_data["token"],
                refresh_token=token_data["refresh_token"],
                token_uri=token_data["token_uri"],
                client_id=token_data["client_id"],
                client_secret=token_data["client_secret"],
                scopes=token_data["scopes"]
            )

        if not creds:
            raise Exception("YouTube credentials not found")

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

            # with open(TOKEN_FILE, "w") as token:
            #     token.write(creds.to_json())
            try:
                setting = Setting.objects.filter(key="youtube_token").first()
                user_id = None

                if setting:
                    old_data = json.loads(setting.value)
                    user_id = old_data.get("user_id")

                YouTubeClient.save_to_db(creds, user_id=user_id)
            except Exception as e:
                print("Failed to update DB token:", str(e))

        youtube = build("youtube", "v3", credentials=creds)

        return youtube