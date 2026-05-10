from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from ..middlewares.permissions import IsSuperUser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from ..middlewares.authentications import BearerTokenAuthentication
from ..serializers import CustomerAddressSerializer
from ..services.ai_service import AiService
from ..models import CustomerAddress

class CustomerViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_permissions(self):
        if self.action in ["ocr", "fetch_honeys"]:
            permission_classes = [AllowAny]
        elif self.action in ["create_address"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsSuperUser]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"], url_path="create-address")
    def create_address(self, request):
        try:
            serializer = CustomerAddressSerializer(data=request.data, context={"request": request})
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Data alamat customer tidak valid.",
                    "errors": serializer.errors,
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Alamat customer berhasil disimpan.",
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="ocr")
    def ocr(self, request):
        try:
            image = request.FILES.get("image")
            if not image:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Field image wajib diisi.",
                }, status=status.HTTP_400_BAD_REQUEST)

            allowed_types = ["image/jpeg", "image/png", "image/webp"]
            if getattr(image, "content_type", None) not in allowed_types:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Format gambar harus JPG, PNG, atau WEBP.",
                }, status=status.HTTP_400_BAD_REQUEST)

            max_size_mb = 8
            if image.size > max_size_mb * 1024 * 1024:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": f"Ukuran gambar maksimal {max_size_mb}MB.",
                }, status=status.HTTP_400_BAD_REQUEST)

            extracted = AiService.extract_customer_address_from_image(image)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Data alamat berhasil diekstrak dari gambar.",
                "data": extracted,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
