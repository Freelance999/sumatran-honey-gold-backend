from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, NotAuthenticated, AuthenticationFailed

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, PermissionDenied):
            response.data = {
                "status": 403,
                "message": str(exc.detail)
            }
        elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            response.data = {
                "status": 401,
                "message": str(exc.detail)
            }
    return response