from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from ..middlewares.authentications import BearerTokenAuthentication
from ..models import Role, School, Teacher, UserDocument
from ..services.storage_service import StorageService
from ..middlewares.permissions import IsSuperUser
from ..serializers import TeacherSerializer
from ..constants.role import Role as RoleConstant

class TeacherViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_permissions(self):
        if self.action in ["create"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["approve_teacher", "fetch_teachers"]:
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
            full_name = (request.data.get("full_name") or "").strip()
            school = (request.data.get("school") or "").strip()
            email = (request.data.get("email") or "").strip().lower()
            whatsapp = (request.data.get("phone_number") or "").strip()

            if not full_name or not school or not email or not whatsapp:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Field full_name, school, email, dan whatsapp wajib diisi.",
                }, status=status.HTTP_400_BAD_REQUEST)

            User = get_user_model()
            if User.objects.filter(email=email).exists():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Email already exists",
                }, status=status.HTTP_400_BAD_REQUEST)

            upload_files = []
            upload_files.extend(request.FILES.getlist("files"))
            for key in request.FILES.keys():
                if key != "files":
                    upload_files.extend(request.FILES.getlist(key))

            if upload_files:
                storage_result = StorageService.upload_media(upload_files)
                if storage_result.get("status") != status.HTTP_200_OK:
                    return Response({
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": storage_result.get("message") or "Gagal upload dokumen.",
                    }, status=status.HTTP_400_BAD_REQUEST)
                uploaded_media_urls = storage_result.get("data", [])
            else:
                uploaded_media_urls = []

            try:
                role_instance = Role.objects.get(id_role=RoleConstant.TEACHER.value)
            except Role.DoesNotExist:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Role teacher tidak ditemukan",
                }, status=status.HTTP_400_BAD_REQUEST)

            name_parts = full_name.split()
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
            username = self._build_unique_username(User, email=email, full_name=full_name)

            with transaction.atomic():
                user = User.objects.create(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role=role_instance,
                    phone_number=whatsapp,
                    is_active=False,
                )
                user.set_unusable_password()
                user.save()

                school, _ = School.objects.get_or_create(name=school)
                teacher = Teacher.objects.create(user=user)
                teacher.school.add(school)

                document_types = [
                    "identity_card",
                    "certificate",
                    "support_document",
                ]

                for index, url in enumerate(uploaded_media_urls):
                    UserDocument.objects.create(
                        user=user,
                        url=url,
                        type=document_types[index] if index < len(document_types) else "other",
                    )

            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Pengajuan registrasi guru berhasil dikirim.",
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="fetch-teachers")
    def fetch_teachers(self, request):
        try:
            teachers = (
                Teacher.objects
                .select_related("user", "mentor")
                .prefetch_related("school")
                .order_by("-updated_at")
            )

            serializer = TeacherSerializer(teachers, many=True, context={"request": request})

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Teachers fetched successfully.",
                "data": serializer.data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="approve-teacher")
    def approve_teacher(self, request):
        try:
            teacher_id = request.data.get("teacher_id")
            password = request.data.get("password")

            if not teacher_id:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Field teacher_id wajib diisi.",
                }, status=status.HTTP_400_BAD_REQUEST)

            if not password:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Field password wajib diisi.",
                }, status=status.HTTP_400_BAD_REQUEST)

            teachers = Teacher.objects.select_related("user", "user__role", "mentor")
            try:
                teacher = teachers.get(id=teacher_id)
            except (Teacher.DoesNotExist, ValueError):
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "Teacher tidak ditemukan.",
                }, status=status.HTTP_404_NOT_FOUND)

            user = teacher.user
            if not user:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Teacher tidak memiliki user.",
                }, status=status.HTTP_400_BAD_REQUEST)

            user_role = getattr(user, "role", None)
            if not user_role or user_role.id_role != RoleConstant.TEACHER.value:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "User yang dipilih bukan akun teacher.",
                }, status=status.HTTP_400_BAD_REQUEST)

            if user.is_active and user.has_usable_password():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Pengajuan akun teacher ini sudah di-approve.",
                }, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.is_active = True
            user.save(update_fields=["password", "is_active"])

            serializer = TeacherSerializer(teacher, context={"request": request})

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Pengajuan akun teacher berhasil di-approve.",
                "data": serializer.data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
