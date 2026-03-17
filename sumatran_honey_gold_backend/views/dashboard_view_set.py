from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..middlewares.authentications import BearerTokenAuthentication
from ..middlewares.permissions import IsSuperUser
from ..models import LiveHarvest, HoneyBatch, HoneyBottle
from ..serializers import LiveHarvestSerializer, BlockSerializer

class DashboardViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in []:
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
                    "colony_health": 0,
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
