import requests
from django.conf import settings


class StorageService:
    @staticmethod
    def upload_media(files):
        if not files:
            return {
                "status": 400,
                "message": "Invalid form data",
                "data": [],
            }

        base_url = (settings.URL_STORAGE or "").rstrip("/")
        if not base_url:
            return {
                "status": 500,
                "message": "URL_STORAGE is not configured",
                "data": [],
            }

        endpoint = f"{base_url}/upload"
        multipart_files = []

        for file_obj in files:
            multipart_files.append(
                (
                    "files",
                    (
                        file_obj.name,
                        file_obj,
                        getattr(file_obj, "content_type", "application/octet-stream"),
                    ),
                )
            )

        try:
            response = requests.post(endpoint, files=multipart_files, timeout=30)
            payload = response.json()
            return {
                "status": payload.get("status", response.status_code),
                "message": payload.get("message", ""),
                "data": payload.get("data", []),
            }
        except requests.RequestException as exc:
            return {
                "status": 500,
                "message": f"Failed to upload media: {exc}",
                "data": [],
            }
        except ValueError:
            return {
                "status": response.status_code,
                "message": "Invalid response from storage service",
                "data": [],
            }