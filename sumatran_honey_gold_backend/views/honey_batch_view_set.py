import qrcode
from io import BytesIO
from django.db import transaction
from django.utils.text import slugify
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.files.base import ContentFile
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser
from ..serializers import HoneyBatchSerializer, HoneyBottleSerializer, InventorySerializer
from ..models import HoneyBatch, HoneyBottle, Inventory

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
            brand_id = request.data.get("brand_id")
            quantity = request.data.get("quantity")
            bottle_size_ml = request.data.get("bottle_size_ml")

            if not all([bottling_id, brand_id, quantity, bottle_size_ml]):
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "bottling_id, brand_id, quantity, and bottle_size_ml are required."
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

            with transaction.atomic():
                honey_batch = HoneyBatch.objects.create(
                    bottling_id=bottling_id,
                    brand_id=brand_id,
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

                for index in range(1, quantity + 1):
                    sequence_number = last_sequence + index
                    serial = f"{serial_prefix}-{sequence_number:0{sequence_padding}d}"

                    bottle = HoneyBottle.objects.create(
                        honey_batch=honey_batch,
                        serial_number=serial
                    )

                    qr_url = f"https://yourdomain.com/verify/{serial}"

                    qr = qrcode.make(qr_url)

                    buffer = BytesIO()
                    qr.save(buffer, format="PNG")

                    bottle.qr_code.save(
                        f"{serial}.png",
                        ContentFile(buffer.getvalue()),
                        save=True
                    )

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