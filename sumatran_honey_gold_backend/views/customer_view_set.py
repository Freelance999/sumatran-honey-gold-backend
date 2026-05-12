from django.conf import settings
from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from ..serializers import CustomerAddressSerializer, GeneralSerializer
from ..middlewares.authentications import BearerTokenAuthentication
from ..constants.cache_key import CacheKey as CacheKeyConstant
from ..services.weather_service import WeatherService
from ..constants.route import Route as RouteConstant
from ..constants.general_category import GeneralCategory as GeneralCategoryConstant
from ..middlewares.permissions import IsSuperUser
from ..models import CustomerAddress, General
from ..services.ai_service import AiService

weather_service = WeatherService()
ai_service = AiService()

class CustomerViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    station_monitoring_route = RouteConstant.STATION_MONITORING
    station_monitoring_categories = [
        GeneralCategoryConstant.PURITY_PREDICTION,
        GeneralCategoryConstant.LAND_TEMPERATURE,
        GeneralCategoryConstant.COLONY_VITALITY,
    ]

    @staticmethod
    def _to_float(value, fallback=None):
        try:
            if value is None or value == "":
                return fallback
            return float(value)
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _clamp(value, minimum=0, maximum=100):
        return max(minimum, min(maximum, value))

    def _fetch_weather(self, request):
        latitude = request.query_params.get("latitude") or getattr(settings, "LATITUDE", None)
        longitude = request.query_params.get("longitude") or getattr(settings, "LONGITUDE", None)

        weather = weather_service.get_weather(latitude, longitude)
        return {
            "temperature": self._to_float(weather.get("temperature"), 31.4),
            "humidity": self._to_float(weather.get("humidity"), 62),
            "wind_speed": self._to_float(weather.get("wind_speed"), 0),
            "rain": self._to_float(weather.get("rain"), 0),
            "uv": self._to_float(weather.get("uv"), 6),
        }

    def _fetch_station_monitoring_urls(self, request):
        route = request.query_params.get("route") or self.station_monitoring_route
        route_options = {route}

        if route.startswith("/"):
            route_options.add(route.lstrip("/"))
        else:
            route_options.add(f"/{route}")

        generals = General.objects.filter(
            route__in=route_options,
            category__in=self.station_monitoring_categories,
        ).order_by("category", "created_at", "id")
        serialized = GeneralSerializer(generals, many=True, context={"request": request}).data

        urls_by_category = {
            category: [] for category in self.station_monitoring_categories
        }
        for item in serialized:
            category = item.get("category")
            if category in urls_by_category:
                urls_by_category[category].append(item)

        return urls_by_category

    def _build_station_monitoring_cards(self, request):
        weather = self._fetch_weather(request)
        urls_by_category = self._fetch_station_monitoring_urls(request)

        temperature = weather["temperature"]
        humidity = weather["humidity"]
        wind_speed = weather["wind_speed"]
        rain = weather["rain"]

        moisture_content = round(self._clamp(16.8 + (humidity * 0.025) + (rain * 0.5), 12, 25), 1)
        diastase_enzyme = round(self._clamp(14.2 - max(moisture_content - 18, 0) * 0.6 - (rain * 0.2), 8, 20), 1)
        purity_prediction = round(self._clamp(100 - max(moisture_content - 18, 0) * 1.2 - (rain * 0.4)), 1)

        air_quality = round(self._clamp(100 - max(humidity - 70, 0) * 0.25 - max(wind_speed - 18, 0) * 0.4 - (rain * 3)))
        colony_frequency = round(self._clamp(220 + ((temperature - 30) * 8) - (rain * 10), 180, 280))
        flight_activity = round(self._clamp(100 - max(humidity - 75, 0) * 0.35 - max(wind_speed - 18, 0) * 0.5 - (rain * 4)))

        return [
            {
                "main_value": purity_prediction,
                "first_value": diastase_enzyme,
                "second_value": moisture_content,
                "urls": urls_by_category["purity_prediction"],
            },
            {
                "main_value": round(temperature, 1),
                "first_value": round(humidity),
                "second_value": air_quality,
                "urls": urls_by_category["land_temperature"],
            },
            {
                "main_value": None,
                "first_value": colony_frequency,
                "second_value": flight_activity,
                "urls": urls_by_category["colony_vitality"],
            },
        ]

    def get_permissions(self):
        if self.action in ["ocr", "fetch_honeys", "fetch_station_monitorings", "fetch_station_monitoring_ai"]:
            permission_classes = [AllowAny]
        elif self.action in ["create_address"]:
            permission_classes = [IsAuthenticated]
        elif self.action in ["create_station_monitoring"]:
            permission_classes = [IsSuperUser]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"], url_path="create-address")
    def create_address(self, request):
        try:
            serializer = CustomerAddressSerializer(data=request.data, context={"request": request})
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Data alamat customer tidak valid.",
                    "errors": serializer.errors,
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Alamat customer berhasil disimpan.",
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path="ocr")
    def ocr(self, request):
        try:
            image = request.FILES.get("image")
            if not image:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Field image wajib diisi.",
                }, status=status.HTTP_400_BAD_REQUEST)

            allowed_types = ["image/jpeg", "image/png", "image/webp"]
            if getattr(image, "content_type", None) not in allowed_types:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Format gambar harus JPG, PNG, atau WEBP.",
                }, status=status.HTTP_400_BAD_REQUEST)

            max_size_mb = 8
            if image.size > max_size_mb * 1024 * 1024:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": f"Ukuran gambar maksimal {max_size_mb}MB.",
                }, status=status.HTTP_400_BAD_REQUEST)

            extracted = AiService.extract_customer_address_from_image(image)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Data alamat berhasil diekstrak dari gambar.",
                "data": extracted,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="station-monitoring")
    def fetch_station_monitorings(self, request):
        try:
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Station monitoring data retrieved successfully",
                "data": self._build_station_monitoring_cards(request),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="station-monitoring-ai")
    def fetch_station_monitoring_ai(self, request):
        try:
            cached = cache.get(CacheKeyConstant.STATION_MONITORING_ANALYSIS.value)

            if cached:
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Analisis station monitoring (cached).",
                    "data": cached
                }, status=status.HTTP_200_OK)

            station_monitorings = self._build_station_monitoring_cards(request)
            analysis = ai_service.analyze_station_monitoring(station_monitorings)

            cache.set(CacheKeyConstant.STATION_MONITORING_ANALYSIS.value, analysis, timeout=3600)

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Station monitoring AI analysis retrieved successfully",
                "data": analysis,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)