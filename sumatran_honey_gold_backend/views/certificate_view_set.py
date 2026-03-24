from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser
from ..serializers import CertificateSerializer
from ..models import Certificate

class CertificateViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["test"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["create", "destroy"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def create(self, request):
        try:
            honey_batch_id = request.data.get("honey_batch_id")
            if not honey_batch_id:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "honey_batch_id is required",
                }, status=status.HTTP_400_BAD_REQUEST)

            files = request.FILES.getlist("files") or request.FILES.getlist("file")
            if not files:
                single_file = request.FILES.get("file") or request.FILES.get("files")
                if single_file:
                    files = [single_file]

            if not files:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "At least one file is required",
                }, status=status.HTTP_400_BAD_REQUEST)

            def _get_list(field_name):
                if hasattr(request.data, "getlist"):
                    return request.data.getlist(field_name)
                value = request.data.get(field_name)
                return [value] if value is not None else []

            titles = _get_list("title")
            descriptions = _get_list("description")
            dates = _get_list("date")

            created = []
            errors = []

            for idx, file_obj in enumerate(files):
                title = titles[idx] if idx < len(titles) else None
                description = descriptions[idx] if idx < len(descriptions) else None
                date = dates[idx] if idx < len(dates) else None

                data = {
                    "honey_batch": honey_batch_id,
                    "title": title,
                    "description": description,
                    "date": date,
                    "file": file_obj,
                }

                serializer = CertificateSerializer(data=data)
                if not serializer.is_valid():
                    errors.append({"index": idx, "errors": serializer.errors})
                    continue

                certificate = serializer.save()
                created.append({
                    "id": certificate.id,
                    "honey_batch_id": certificate.honey_batch_id,
                    "title": certificate.title,
                    "description": certificate.description,
                    "date": certificate.date,
                    "file_url": request.build_absolute_uri(certificate.file.url) if certificate.file else None,
                    "created_at": certificate.created_at,
                    "updated_at": certificate.updated_at,
                })

            return Response({
                "status": status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST,
                "message": "Certificates created successfully" if created else "Failed to create certificates",
                "data": created,
            }, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        try:
            if not pk:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Certificate ID is required",
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                certificate = Certificate.objects.get(pk=pk)
            except Certificate.DoesNotExist:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Certificate not found",
                }, status=status.HTTP_404_NOT_FOUND)

            certificate.delete()

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Certificate deleted successfully",
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["post"], url_path="test")
    def test(self, request):
        try:
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Test successful",
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)