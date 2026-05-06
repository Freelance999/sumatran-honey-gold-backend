from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser
from ..middlewares.authentications import BearerTokenAuthentication
from ..models import UserToken, RefreshToken, Role as RoleModel, School, Teacher
from ..services.storage_service import StorageService
from ..middlewares.permissions import IsSuperUser
from ..serializers import UserSerializer
from ..constants.role import Role as RoleConstant

class UserViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["create", "register_teacher"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["fetch_users"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @staticmethod
    def _build_unique_username(User, email, full_name):
        base_candidate = (email or "").split("@")[0].strip().lower()
        if not base_candidate:
            base_candidate = "-".join((full_name or "").strip().lower().split())
        if not base_candidate:
            base_candidate = "teacher"
        base_candidate = base_candidate.replace(" ", "-")
        username = base_candidate
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_candidate}{counter}"
            counter += 1
        return username
    
    def create(self, request):
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            first_name = request.data.get('first_name', '')
            is_staff = request.data.get('is_staff', False)
            is_superuser = request.data.get('is_superuser', False)
            id_role = request.data.get('id_role')

            if not id_role:
                id_role = RoleConstant.CONSUMER.value

            try:
                role_instance = RoleModel.objects.get(id_role=id_role)
            except RoleModel.DoesNotExist:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Role tidak ditemukan"
                }, status=status.HTTP_400_BAD_REQUEST)
            
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
            request_data['role'] = role_instance.id

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
                user.role = role_instance
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

    @action(detail=False, methods=["post"], url_path="fetch-users")
    def fetch_users(self, request):
        try:
            User = get_user_model()

            is_active_param = request.query_params.get("is_active")
            users = User.objects.select_related("role").order_by("-date_joined")

            if is_active_param is not None:
                is_active_user = is_active_param.lower() == "true"
                users = users.filter(is_active=is_active_user)

            serializer = UserSerializer(users, many=True, context={"request": request})

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Users fetched successfully.",
                "data": serializer.data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
