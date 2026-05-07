from datetime import timedelta
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import LiveHarvest, HoneyBatch, HoneyBottle, WeatherObservation
from ..middlewares.authentications import BearerTokenAuthentication
from ..serializers import LiveHarvestSerializer, BlockSerializer
from ..services.weather_service import WeatherService
from ..middlewares.permissions import IsSuperUser
from ..services.ai_service import AiService
from ..constants.cache_key import CacheKey as CacheKeyConstant

class DashboardViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in ["fetch_system_alerts"]:
            permission_classes = [AllowAny]
        elif self.action in []:
            permission_classes = [IsSuperUser]
        elif self.action in ["fetch_kpis", "fetch_live_and_ledger"]:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"], url_path="kpis")
    def fetch_kpis(self, request):
        try:
            now = timezone.now()

            weather = WeatherObservation.objects.filter(observed_at__gte=now - timedelta(hours=24))
            base_score = WeatherService.calculate_base_score(weather)

            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start_of_month.month == 12:
                next_month = start_of_month.replace(year=start_of_month.year + 1, month=1)
            else:
                next_month = start_of_month.replace(month=start_of_month.month + 1)

            total_panen_kg = (
                HoneyBatch.objects.filter(created_at__gte=start_of_month, created_at__lt=next_month)
                .aggregate(total=Sum("weight"))
                .get("total")
            ) or 0

            botol_siap_jual = HoneyBottle.objects.filter(serial_number__isnull=False).exclude(serial_number="").count()

            return Response({
                "status": status.HTTP_200_OK,
                "message": "KPIS Fetched Successfully",
                "data": {
                    "total_harvest_this_month": total_panen_kg,
                    "bottles_ready_for_sel": botol_siap_jual,
                    "colony_health": base_score,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["post"], url_path="live-and-ledger")
    def fetch_live_and_ledger(self, request):
        try:
            live = (
                LiveHarvest.objects.filter(status__iexact="LIVE").order_by("-start_time").first()
            )
            if not live:
                live = (
                    LiveHarvest.objects.filter(status__iexact="STOPPED")
                    .order_by("-end_time", "-updated_at")
                    .first()
                )

            if live:
                live_data = LiveHarvestSerializer(live).data
                live_data["block"] = BlockSerializer(live.block).data if live.block else None
            else:
                live_data = None

            ledgers = []
            batches = (
                HoneyBatch.objects.select_related("live_harvest", "live_harvest__block")
                .order_by("-created_at")
            )
            for batch in batches:
                live_harvest = batch.live_harvest
                block = live_harvest.block if live_harvest else None
                youtube_video_id = live_harvest.youtube_video_id if live_harvest else None

                if live_harvest and live_harvest.start_time:
                    tanggal = live_harvest.start_time
                else:
                    tanggal = batch.created_at

                ledgers.append({
                    "batch_id": batch.batch_id,
                    "date": tanggal.isoformat() if tanggal else None,
                    "code": block.code if block and block.code else (block.name if block else None),
                    "weight": batch.weight or 0,
                    "status": batch.status,
                    "youtube_live_url": (
                        f"https://www.youtube.com/watch?v={youtube_video_id}" if youtube_video_id else None
                    ),
                })

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Live & Ledger Fetched Successfully",
                "data": {
                    "live": live_data,
                    "production_ledgers": ledgers,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["post"], url_path="system-alert")
    def fetch_system_alerts(self, request):
        try:
            cache_key = "system_alerts_latest"

            cached = cache.get(cache_key)
            if cached:
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "System alerts (cached)",
                    "data": cached
                }, status=status.HTTP_200_OK)
        
            now = timezone.now()
            recent_weather = WeatherObservation.objects.filter(
                observed_at__gte=now - timedelta(hours=24)
            ).order_by("-observed_at")[:100]

            latest_live = LiveHarvest.objects.order_by("-created_at").first()
            recent_batches = HoneyBatch.objects.order_by("-created_at")[:20]

            weather_data = [
                {
                    "temp": w.temperature,
                    "humidity": w.humidity,
                    "wind": w.wind_speed,
                    "time": w.observed_at.isoformat() if w.observed_at else None
                }
                for w in recent_weather
            ]

            live_data = {
                "status": latest_live.status if latest_live else None,
                "temperature": latest_live.weather_temperature if latest_live else None,
                "humidity": latest_live.weather_humidity if latest_live else None,
            }

            batch_data = [
                {
                    "weight": b.weight,
                    "status": b.status
                }
                for b in recent_batches
            ]

            # Comment kalau gamau pakai rule
            rule_alerts = AiService.generate_rule_based_alerts(
                weather_data, live_data, batch_data
            )

            use_ai = False

            if len(rule_alerts) < 2:
                use_ai = True
            elif any(a["level"] == "critical" for a in rule_alerts):
                use_ai = True

            final_alerts = rule_alerts

            if use_ai:
                prompt = AiService.build_prompt(weather_data, live_data, batch_data)
                ai_alerts = AiService.generate_alerts(prompt)

                final_alerts.extend(ai_alerts)

            final_alerts = final_alerts[:5]

            if not final_alerts:
                final_alerts = [{
                    "level": "info",
                    "title": "Sistem Normal",
                    "message": "Tidak ditemukan anomali signifikan",
                    "recommendation": "Lanjutkan monitoring"
                }]
            # Comment kalau gamau pakai rule

            # Uncomment kalau gamau pakai rule
            # prompt = AiService.build_prompt(weather_data, live_data, batch_data)
            # final_alerts = AiService.generate_alerts(prompt)
            # Uncomment kalau gamau pakai rule
            
            cache.set(CacheKeyConstant.SYSTEM_ALERTS_LATESTS.value, final_alerts, timeout=3600)

            return Response({
                "status": status.HTTP_200_OK,
                "message": "System alerts generated",
                "data": final_alerts,
            })

        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)