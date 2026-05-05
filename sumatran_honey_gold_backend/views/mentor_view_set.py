from decimal import Decimal
from django.db.models import Sum
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from ..middlewares.authentications import BearerTokenAuthentication
from ..models import Teacher, MentorPersonalOrder
from ..services.ai_service import AiService
from ..constants.role import Role

COMMISSION_RATE = Decimal("0.05")


def _is_mentor(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = getattr(user, "role", None)
    return bool(role and role.id_role == Role.MENTOR.value)


def _teacher_display_name(teacher: Teacher) -> str:
    u = teacher.user
    if not u:
        return ""
    full = (u.get_full_name() or "").strip()
    if full:
        return full
    return u.username or ""


def _primary_school_name(teacher: Teacher) -> str:
    links = list(teacher.teacher_schools.all())
    if not links:
        return ""
    links.sort(
        key=lambda ts: (
            (ts.school.name or "") if getattr(ts, "school", None) else "",
            ts.id,
        )
    )
    sch = links[0].school
    return (sch.name or "").strip() if sch else ""


def build_mentor_statistics_payload(mentor_user):
    """Montir payload mentor_commission / mentor_income / mentor_network untuk response & AI."""
    teachers = (
        Teacher.objects.filter(mentor=mentor_user)
        .select_related("user")
        .prefetch_related("teacher_schools__school")
    )

    commission_rows = []
    for t in teachers:
        omzet = t.omzet or 0
        commission = int(Decimal(omzet) * COMMISSION_RATE)
        commission_rows.append(
            {
                "teacher": t,
                "teacher_name": _teacher_display_name(t),
                "school": _primary_school_name(t),
                "commission": commission,
            }
        )

    total_commission = sum(r["commission"] for r in commission_rows)
    commission_rows.sort(key=lambda r: r["commission"], reverse=True)
    top_commission = commission_rows[:3]
    commission_details = [
        {
            "teacher_name": r["teacher_name"],
            "school": r["school"] or "",
            "commission": r["commission"],
        }
        for r in top_commission
    ]

    orders = MentorPersonalOrder.objects.filter(mentor=mentor_user)

    income_total = orders.aggregate(s=Sum("line_total"))["s"] or 0

    product_agg = (
        orders.values("product_name", "weight")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:3]
    )
    income_details = [
        {
            "product_name": row["product_name"] or "",
            "weight": row["weight"],
            "total": row["total_qty"] or 0,
        }
        for row in product_agg
    ]

    people_qs = orders.filter(buyer_type=MentorPersonalOrder.BuyerType.PEOPLE)
    people_distinct_ref = people_qs.exclude(buyer_reference="").values("buyer_reference").distinct().count()
    people_no_ref = people_qs.filter(buyer_reference="").count()
    people_count = people_distinct_ref + people_no_ref

    school_count = (
        orders.filter(
            buyer_type=MentorPersonalOrder.BuyerType.SCHOOL,
            school_id__isnull=False,
        )
        .values("school_id")
        .distinct()
        .count()
    )

    network_total = people_count + school_count
    network_details = [
        {"type": "people", "total": people_count},
        {"type": "school", "total": school_count},
    ]

    return {
        "mentor_commission": {
            "total": int(total_commission),
            "total_teacher": teachers.count(),
            "details": commission_details,
        },
        "mentor_income": {
            "total": int(income_total),
            "details": income_details,
        },
        "mentor_network": {
            "total": int(network_total),
            "details": network_details,
        },
    }


class MentorViewSet(viewsets.ViewSet):
    authentication_classes = [BearerTokenAuthentication]

    def get_permissions(self):
        if self.action in []:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["post"], url_path="fetch-statistic")
    def fetch_statistic(self, request):
        try:
            if not _is_mentor(request.user):
                return Response(
                    {
                        "status": status.HTTP_403_FORBIDDEN,
                        "message": "Hanya akun mentor yang dapat mengakses statistik ini.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            data = build_mentor_statistics_payload(request.user)

            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": "Statistik mentor berhasil diambil.",
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="fetch-statistical-analysis")
    def fetch_statistical_analysis(self, request):
        try:
            if not _is_mentor(request.user):
                return Response(
                    {
                        "status": status.HTTP_403_FORBIDDEN,
                        "message": "Hanya akun mentor yang dapat mengakses analisis ini.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            statistics = build_mentor_statistics_payload(request.user)
            analysis = AiService.analyze_mentor_statistics(statistics)

            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": "Analisis statistik berhasil dihasilkan.",
                    "data": analysis,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "message": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
