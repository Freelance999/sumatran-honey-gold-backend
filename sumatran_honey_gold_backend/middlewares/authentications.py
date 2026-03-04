from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.timezone import now
from ..models import UserToken

class BearerTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)

        if not auth_header:
            return None

        try:
            auth = auth_header.split()

            if auth[0].lower() != 'bearer':
                return None 

            token_key = auth[1]
            token = getattr(request, 'auth_token', None)

            if not token:
                token = UserToken.objects.select_related('user').get(key=token_key)
                request.auth_token = token

            if token.is_expired():
                raise AuthenticationFailed('Token expired')

            token.last_used = now()
            token.save(update_fields=['last_used'])

            return (token.user, token)
        
        except UserToken.DoesNotExist:
            raise AuthenticationFailed('Invalid or expired token')
        except (IndexError, ValueError):
            raise AuthenticationFailed('Invalid token format')