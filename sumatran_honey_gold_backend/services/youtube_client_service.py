import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_FILE = "youtube_token.json"

class YouTubeClient:

    @staticmethod
    def get_client():
        creds = None

        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE)

        if not creds:
            raise Exception("YouTube credentials not found")

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        youtube = build("youtube", "v3", credentials=creds)

        return youtube