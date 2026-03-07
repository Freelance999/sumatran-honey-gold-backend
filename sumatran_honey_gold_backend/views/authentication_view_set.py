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

class AuthenticationViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["login"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in []:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        try:
            User = get_user_model()
            email_or_username = request.data.get('email_or_username')
            password = request.data.get('password')
            
            if not email_or_username or not password:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Email or username and password are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = None
            try:
                if '@' in email_or_username:
                    user = User.objects.get(email=email_or_username)
                else:
                    user = User.objects.get(username=email_or_username)
            except User.DoesNotExist:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "User not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            if not user.check_password(password):
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid password"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not user.is_active:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "User account is disabled"
                }, status=status.HTTP_403_FORBIDDEN)
            
            access = UserToken.objects.create(user=user)
            refresh = RefreshToken.objects.create(user=user)

            serializer = UserSerializer(instance=user)
            data = serializer.data
            data['access_token'] = access.key
            data['refresh_token'] = refresh.key

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Login Successfully",
                "data": data,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)