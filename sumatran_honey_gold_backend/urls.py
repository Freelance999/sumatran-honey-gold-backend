from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views.authentication_view_set import AuthenticationViewSet
from .views.live_harvest_view_set import LiveHarvestViewSet
from .views.honey_bottle_view_set import HoneyBottleViewSet
from .views.certificate_view_set import CertificateViewSet
from .views.weather_view_set import WeatherViewSet
from .views.client_view_set import ClientViewSet
from .views.user_view_set import UserViewSet

router = DefaultRouter()

router.register(r"user", UserViewSet, basename="user")
router.register(r"authentication", AuthenticationViewSet, basename="authentication")
router.register(r"live-harvest", LiveHarvestViewSet, basename="live-harvest")
router.register(r"client", ClientViewSet, basename="client")
router.register(r"honey-bottle", HoneyBottleViewSet, basename="honey-bottle")
router.register(r"certificate", CertificateViewSet, basename="certificate")
router.register(r"weather", WeatherViewSet, basename="weather")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/sumatran-honey-gold/v1/', include(router.urls)),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)