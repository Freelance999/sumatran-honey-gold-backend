from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views.authentication_view_set import AuthenticationViewSet
from .views.live_harvest_view_set import LiveHarvestViewSet
from .views.user_view_set import UserViewSet

router = DefaultRouter()

router.register(r"user", UserViewSet, basename="user")
router.register(r"authentication", AuthenticationViewSet, basename="authentication")
router.register(r"live-harvest", LiveHarvestViewSet, basename="live-harvest")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/sumatran-honey-gold/v1/', include(router.urls)),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)