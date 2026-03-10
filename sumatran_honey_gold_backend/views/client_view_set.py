from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser
from ..serializers import ClientSerializer
from ..models import Client

class ClientViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in []:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["upload_logo", "create", "list", "update_logo"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
    def create(self, request):
        try:
            serializer = ClientSerializer(data=request.data)

            if serializer.is_valid():
                client = serializer.save()
                client.save()
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Client Created Successfully",
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
        
    def list(self, request):
        try:
            page = int(request.GET.get('page'))
            page_size = int(request.GET.get('page_size'))
            query_param = request.GET.get("query", "").strip()

            clients = Client.objects.all()
            
            if query_param:
                clients = clients.filter(name__icontains=query_param)
            
            clients = clients.order_by('-updated_at')
            client_serializer = ClientSerializer(clients, many=True)
            data = client_serializer.data
            start = (page - 1) * page_size
            end = start + page_size
            data = data[start:end]

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Clients fetched successfully.",
                "total_item": len(data),
                "page": page,
                "page_size": page_size,
                "total_page": (clients.count() + page_size - 1) // page_size,
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["post"], url_path="upload-logo")
    def upload_logo(self, request):
        try:
            image_file = request.FILES.get('image')
            client_id = request.data.get("client_id")

            if not image_file:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Image Is Required",
                }, status=status.HTTP_400_BAD_REQUEST)

            if not client_id:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Client ID Is Required",
                }, status=status.HTTP_400_BAD_REQUEST)
            
            client = Client.objects.get(id=client_id)
            client.logo = image_file
            client.save(update_fields=["logo", "updated_at"])

            request.build_absolute_uri(client.logo.url) if client.logo else None

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Logo Uploaded Successfully",
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["put"], url_path="update-logo")
    def update_logo(self, request):
        try:
            image_file = request.FILES.get("image")
            client_id = request.data.get("client_id")

            if not image_file:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Image Is Required",
                }, status=status.HTTP_400_BAD_REQUEST)

            if not client_id:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Client ID Is Required",
                }, status=status.HTTP_400_BAD_REQUEST)

            client = Client.objects.get(id=client_id)
            client.logo = image_file
            client.save(update_fields=["logo", "updated_at"])

            request.build_absolute_uri(client.logo.url) if client.logo else None

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Logo Updated Successfully",
            }, status=status.HTTP_200_OK)

        except Client.DoesNotExist:
            return Response(
                {"status": status.HTTP_404_NOT_FOUND, "message": "Client Not Found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": status.HTTP_500_INTERNAL_SERVER_ERROR, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )