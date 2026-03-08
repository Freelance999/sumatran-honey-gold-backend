from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from rest_framework.permissions import IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser
from ..models import UserToken, RefreshToken, PasswordResetToken
from ..serializers import UserSerializer

class AuthenticationViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["login", "reset_password", "refresh_token"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["logout"]:
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
        
    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request):
        try:
            token = request.auth

            if token and isinstance(token, UserToken):
                user = token.user
                token.delete()
                RefreshToken.objects.filter(user=user).delete()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Logout successfully"
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Token not found"
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["post", "put"], url_path="reset-password")
    def reset_password(self, request):
        try:
            User = get_user_model()

            if request.method == "POST":
                email = request.data.get("email")
                if not email:
                    return Response({
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "email is required"
                    }, status=status.HTTP_400_BAD_REQUEST)

                try:
                    user = User.objects.get(email__iexact=email.strip())
                except User.DoesNotExist:
                    return Response({
                        "status": status.HTTP_200_OK,
                        "message": "If the account exists, a reset link has been sent."
                    }, status=status.HTTP_200_OK)

                PasswordResetToken.objects.filter(custom_user=user, is_used=False).update(is_used=True)
                prt = PasswordResetToken.objects.create(custom_user=user)

                frontend_base = "/create-new-password"
                if frontend_base.startswith("http"):
                    reset_link = f"{frontend_base}?token={prt.token}"
                else:
                    scheme = "https" if request.is_secure() else "http"
                    host = request.get_host()
                    reset_link = f"{scheme}://{host}{frontend_base}?token={prt.token}"

                context = {
                    "user": user,
                    "reset_link": reset_link,
                    "expires_at": prt.expires_at,
                    "app_name": "EMAS MADU SUMATRA",
                }
                subject = f"{context['app_name']} - Reset Your Password"
                from_email = settings.EMAIL_HOST_USER
                html_body = render_to_string("password-reset-email.html", context)
                text_body = f"Use this link to set a new password: {reset_link}"

                try:
                    msg = EmailMultiAlternatives(subject, text_body, from_email, [user.email])
                    msg.attach_alternative(html_body, "text/html")
                    msg.send(fail_silently=True)
                except Exception:
                    pass

                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "If the account exists, a reset link has been sent."
                }, status=status.HTTP_200_OK)

            token = request.data.get("token")
            new_password = request.data.get("new_password")
            if not token or not new_password:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "token and new_password are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                prt = PasswordResetToken.objects.select_related("custom_user").get(token=token)
            except PasswordResetToken.DoesNotExist:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid token"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not prt.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Token expired or already used"
                }, status=status.HTTP_400_BAD_REQUEST)

            user = prt.custom_user
            user.set_password(new_password)
            user.save()

            prt.is_used = True
            prt.save()

            UserToken.objects.filter(user=user).delete()
            RefreshToken.objects.filter(user=user).delete()

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Password has been reset successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="refresh-token")
    def refresh_token(self, request):
        try:
            refresh_key = request.data.get("refresh_token")
            rotate = request.data.get("rotate", True)

            if not refresh_key:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "refresh_token is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                refresh_token = RefreshToken.objects.get(key=refresh_key, is_revoked=False)
            except RefreshToken.DoesNotExist:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid refresh token"
                }, status=status.HTTP_400_BAD_REQUEST)

            if refresh_token.is_expired():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Refresh token expired"
                }, status=status.HTTP_400_BAD_REQUEST)

            user = refresh_token.user
            UserToken.objects.filter(user=user).delete()
            access = UserToken.objects.create(user=user)

            response_data = {
                "access_token": access.key,
            }

            if rotate:
                refresh_token.is_revoked = True
                refresh_token.save(update_fields=['is_revoked'])
                new_refresh_token = RefreshToken.objects.create(user=user)
                response_data['refresh_token'] = new_refresh_token.key
            else:
                response_data['refresh_token'] = refresh_token.key

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Token refreshed successfully",
                "data": response_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)