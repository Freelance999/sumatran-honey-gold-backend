import json
import base64
import hmac
import hashlib
from django.conf import settings

class EncodeDecodeService:
    @staticmethod
    def encode_state(data: dict) -> str:
        payload = json.dumps(data)

        signature = hmac.new(
            settings.SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        state_obj = {
            "payload": payload,
            "sig": signature
        }

        return base64.urlsafe_b64encode(
            json.dumps(state_obj).encode()
        ).decode()

    @staticmethod
    def decode_state(state: str) -> dict:
        try:
            decoded = json.loads(
                base64.urlsafe_b64decode(state.encode()).decode()
            )

            payload = decoded.get("payload")
            sig = decoded.get("sig")

            expected_sig = hmac.new(
                settings.SECRET_KEY.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()

            if sig != expected_sig:
                raise Exception("Invalid state signature")

            return json.loads(payload)

        except Exception as e:
            raise Exception(f"Failed to decode state: {str(e)}")