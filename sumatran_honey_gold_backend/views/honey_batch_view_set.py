import qrcode
from io import BytesIO
from django.conf import settings
from django.db import transaction
from django.utils.text import slugify
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser
from ..services.storage_service import StorageService
from ..serializers import HoneyBatchSerializer, HoneyBottleSerializer, InventorySerializer
from ..models import HoneyBatch, HoneyBottle, HoneyProduct, Inventory

class HoneyBatchViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in []:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["create"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
    def create(self, request):
        try:
            bottling_id = request.data.get("bottling_id")
            honey_product_id = request.data.get("honey_product_id")
            brand_id = request.data.get("brand_id")
            quantity = request.data.get("quantity")
            bottle_size_ml = request.data.get("bottle_size_ml")

            if not all([bottling_id, honey_product_id, quantity]):
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "bottling_id, honey_product_id, and quantity are required."
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                honey_product_id = int(honey_product_id)
            except (TypeError, ValueError):
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "honey_product_id must be a valid integer."
                }, status=status.HTTP_400_BAD_REQUEST)

            product = HoneyProduct.objects.filter(id=honey_product_id).first()
            if not product:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "honey_product_id is invalid."
                }, status=status.HTTP_400_BAD_REQUEST)

            if brand_id:
                try:
                    brand_id = int(brand_id)
                except (TypeError, ValueError):
                    return Response({
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "brand_id must be a valid integer."
                    }, status=status.HTTP_400_BAD_REQUEST)

                if product.brand_id and brand_id != product.brand_id:
                    return Response({
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "brand_id does not match the selected product."
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                brand_id = product.brand_id

            bottle_size_ml = bottle_size_ml or product.bottle_size_ml

            if not brand_id:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "brand_id is required when the selected product has no brand."
                }, status=status.HTTP_400_BAD_REQUEST)

            if not bottle_size_ml:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "bottle_size_ml is required when the selected product has no bottle size."
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "quantity must be a valid integer."
                }, status=status.HTTP_400_BAD_REQUEST)

            if quantity <= 0:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "quantity must be greater than 0."
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                bottle_size_ml = int(bottle_size_ml)
            except (TypeError, ValueError):
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "bottle_size_ml must be a valid integer."
                }, status=status.HTTP_400_BAD_REQUEST)

            if product.bottle_size_ml and bottle_size_ml != product.bottle_size_ml:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "bottle_size_ml does not match the selected product."
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                honey_batch = HoneyBatch.objects.create(
                    bottling_id=bottling_id,
                    brand_id=brand_id,
                    honey_product=product,
                    quantity=quantity
                )

                block = None
                if honey_batch.bottling and honey_batch.bottling.raw_stock and honey_batch.bottling.raw_stock.live_harvest:
                    block = honey_batch.bottling.raw_stock.live_harvest.block

                block_code = slugify((block.code if block and block.code else "unknown").strip())
                block_name = slugify((block.name if block and block.name else "block").strip())
                serial_prefix = f"{block_code}-{block_name}"

                existing_serials = HoneyBottle.objects.filter(
                    serial_number__startswith=f"{serial_prefix}-"
                ).values_list("serial_number", flat=True)

                last_sequence = 0
                for existing_serial in existing_serials:
                    try:
                        current_sequence = int(existing_serial.split("-")[-1])
                        if current_sequence > last_sequence:
                            last_sequence = current_sequence
                    except (TypeError, ValueError, AttributeError):
                        continue

                sequence_padding = max(2, len(str(quantity)))

                bottle_payloads = []
                qr_files = []

                for index in range(1, quantity + 1):
                    sequence_number = last_sequence + index
                    serial = f"{serial_prefix}-{sequence_number:0{sequence_padding}d}"

                    qr_url = f"{settings.BASE_URL_FE}/verify/{serial}"
                    qr = qrcode.make(qr_url)

                    buffer = BytesIO()
                    qr.save(buffer, format="PNG")

                    bottle_payloads.append({
                        "serial_number": serial,
                    })
                    qr_files.append(
                        SimpleUploadedFile(
                            f"{serial}.png",
                            buffer.getvalue(),
                            content_type="image/png"
                        )
                    )

                storage_result = StorageService.upload_media(qr_files)
                uploaded_qr_urls = storage_result.get("data", [])
                if (
                    storage_result.get("status") != status.HTTP_200_OK
                    or len(uploaded_qr_urls) != len(bottle_payloads)
                ):
                    transaction.set_rollback(True)
                    return Response({
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": storage_result.get("message") or "Failed to upload QR code images.",
                    }, status=status.HTTP_400_BAD_REQUEST)

                HoneyBottle.objects.bulk_create([
                    HoneyBottle(
                        honey_batch=honey_batch,
                        serial_number=payload["serial_number"],
                        qr_code=uploaded_qr_urls[index],
                    )
                    for index, payload in enumerate(bottle_payloads)
                ])

                inventory, _ = Inventory.objects.get_or_create(
                    brand_id=brand_id,
                    bottle_size_ml=bottle_size_ml,
                    defaults={"stock": 0}
                )
                inventory.stock = (inventory.stock or 0) + quantity
                inventory.save(update_fields=["stock", "updated_at"])

            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Honey batch created successfully.",
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
