import os
import qrcode
import base64
import binascii
from io import BytesIO
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser
from ..services.storage_service import StorageService
from ..serializers import HoneyBottleSerializer
from ..models import HoneyBottle

class HoneyBottleViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["generate"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["create"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def generate_serial_number(self):
        while True:
            serial = binascii.hexlify(os.urandom(10)).decode().upper()
            if not HoneyBottle.objects.filter(serial_number=serial).exists():
                return serial

    def generate_qr_code(self, qr_data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        try:
            honey_batch_id = request.data.get('honey_batch_id')

            if not honey_batch_id:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "honey_batch_id is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serial_number = self.generate_serial_number()
            qr_data = f"honey_batch_id={honey_batch_id}&serial_number={serial_number}"
            qr_buffer = self.generate_qr_code(qr_data)
            qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "QR code generated successfully",
                "data": {
                    "honey_batch_id": honey_batch_id,
                    "serial_number": serial_number,
                    "qr_code_base64": f"data:image/png;base64,{qr_base64}"
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request):
        try:
            serial_number = request.data.get('serial_number')
            qr_code_base64 = request.data.get('qr_code_base64')
            honey_batch_id = request.data.get('honey_batch_id')

            if not serial_number or not qr_code_base64 or not honey_batch_id:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "serial_number, qr_code_base64, and honey_batch_id are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if qr_code_base64.startswith('data:image/png;base64,'):
                qr_code_base64 = qr_code_base64.replace('data:image/png;base64,', '')
            
            qr_image_data = base64.b64decode(qr_code_base64)
            file_name = f"qr_{serial_number}.png"
            qr_image = SimpleUploadedFile(
                file_name,
                qr_image_data,
                content_type="image/png"
            )
            storage_result = StorageService.upload_media([qr_image])
            uploaded_qr_urls = storage_result.get("data", [])
            if storage_result.get("status") != status.HTTP_200_OK or not uploaded_qr_urls:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": storage_result.get("message") or "Failed to upload QR code image.",
                }, status=status.HTTP_400_BAD_REQUEST)

            data = {
                'honey_batch': honey_batch_id,
                'serial_number': serial_number,
                'qr_code': uploaded_qr_urls[0],
            }
            
            serializer = HoneyBottleSerializer(data=data)

            if serializer.is_valid():
                honey_bottle = serializer.save()
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "QR & serial number saved successfully",
                    "data": {
                        "id": honey_bottle.id,
                        "honey_batch_id": honey_bottle.honey_batch.id,
                        "serial_number": honey_bottle.serial_number,
                        "qr_code_url": honey_bottle.qr_code,
                        "created_at": honey_bottle.created_at,
                        "updated_at": honey_bottle.updated_at,
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
