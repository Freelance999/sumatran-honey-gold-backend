from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser
from ..serializers import UserSerializer
from ..models import UserToken

class UserViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in [""]:
            permission_classes = [AllowAny]
        elif self.action in [""]:
            permission_classes = [IsSuperUser]
        elif self.action in ["create", "list", "update", "retrieve"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
    def create(self, request):
        try:
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Success",
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def list(self, request):
        try:
            data = []
            page = 1
            page_size = 15

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Success",
                "total_item": len(data),
                "page": page,
                "page_size": page_size,
                # "total_page": (blood_pressures.count() + page_size - 1) // page_size,
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)