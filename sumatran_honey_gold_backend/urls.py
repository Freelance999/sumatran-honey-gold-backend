from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from sumatran_honey_gold_backend.views.user_view_set import UserViewSet
from sumatran_honey_gold_backend.views.live_harvest_view_set import LiveHarvestViewSet

router = DefaultRouter()

router.register(r"user", UserViewSet, basename="user")
router.register(r"live-harvest", LiveHarvestViewSet, basename="live-harvest")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/sumatran-honey-gold/v1/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)