from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser
from ..models import UserToken, RefreshToken
from ..serializers import UserSerializer

class UserViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["create"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in []:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
    def create(self, request):
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            first_name = request.data.get('first_name', '')
            is_staff = request.data.get('is_staff', False)
            is_superuser = request.data.get('is_superuser', False)

            name_parts = first_name.strip().split()
            if len(name_parts) > 1:
                processed_first_name = name_parts[0]
                processed_last_name = ' '.join(name_parts[1:])
            else:
                processed_first_name = first_name.strip()
                processed_last_name = ''

            request_data = request.data.copy()
            request_data['first_name'] = processed_first_name
            request_data['last_name'] = processed_last_name

            User = get_user_model()
            if User.objects.filter(username=username).exists():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Username already exists"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(email=email).exists():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Email already exists"
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = UserSerializer(data=request_data)

            if serializer.is_valid():
                user = serializer.save()
                user.set_password(password)
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.save()

                access = UserToken.objects.create(user=user)
                refresh = RefreshToken.objects.create(user=user)
                user_serializer = UserSerializer(instance=user, context={'request': request})
                data = user_serializer.data
                data['access_token'] = access.key
                data['refresh_token'] = refresh.key

                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Account registered successfully",
                    "data": data,
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