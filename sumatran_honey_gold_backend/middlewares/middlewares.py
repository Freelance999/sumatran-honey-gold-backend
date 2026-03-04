from ..models import UserToken
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework import status

class TokenExpiryMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)

        if auth_header:
            try:
                auth = auth_header.split()

                if len(auth) != 2 or auth[0].lower() != 'bearer':
                    return JsonResponse({
                        "status": status.HTTP_401_UNAUTHORIZED,
                        'message': 'Token format must be Bearer <token>'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                token_key = auth[1]
                token = UserToken.objects.select_related('user').get(key=token_key)
                if token.is_expired():
                    return JsonResponse({
                        "status": status.HTTP_401_UNAUTHORIZED,
                        'message': 'Token expired'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                request.auth_token = token

                return None 
                
            except UserToken.DoesNotExist:
                return JsonResponse({
                    "status": status.HTTP_401_UNAUTHORIZED,
                    'message': 'Invalid or expired token'
                }, status=status.HTTP_401_UNAUTHORIZED)
            except (IndexError, ValueError):
                return JsonResponse({
                    "status": status.HTTP_401_UNAUTHORIZED,
                    'message': 'Invalid token format'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
        return None 