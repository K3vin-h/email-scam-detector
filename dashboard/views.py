import logging
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.models import EmailRecord, ScanSettings, SummaryReport
from dashboard.serializers import (
    EmailRecordSerializer,
    ScanSettingsSerializer,
    SummaryReportSerializer,
)

logger = logging.getLogger(__name__)


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class EmailListView(ListAPIView):
    """GET /api/emails/?is_scam=true — paginated email scan results."""

    permission_classes = [IsAuthenticated]
    serializer_class = EmailRecordSerializer

    def get_queryset(self):
        qs = EmailRecord.objects.all()
        is_scam = self.request.query_params.get("is_scam")
        if is_scam is not None:
            value = is_scam.lower()
            if value not in ("true", "false"):
                raise ValidationError(
                    {"is_scam": "Expected 'true' or 'false'."}
                )
            qs = qs.filter(is_scam=value == "true")
        return qs


class ScanSettingsView(APIView):
    """GET/PATCH /api/settings/ — read or partially update the singleton settings row."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        settings = ScanSettings.load()
        return Response(ScanSettingsSerializer(settings).data)

    def patch(self, request):
        settings = ScanSettings.load()
        serializer = ScanSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SummaryReportListView(ListAPIView):
    """GET /api/reports/?period=daily|weekly|monthly — paginated report list."""

    permission_classes = [IsAuthenticated]
    serializer_class = SummaryReportSerializer

    def get_queryset(self):
        qs = SummaryReport.objects.all()
        period = self.request.query_params.get("period")
        if period in ("daily", "weekly", "monthly"):
            qs = qs.filter(period=period)
        return qs


class StatsView(APIView):
    """GET /api/stats/ — aggregate counts for dashboard charts."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        last_7 = now - timedelta(days=7)
        last_30 = now - timedelta(days=30)

        top_senders = list(
            EmailRecord.objects.filter(is_scam=True)
            .values("sender")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        return Response(
            {
                "total_scanned": EmailRecord.objects.count(),
                "total_scams": EmailRecord.objects.filter(is_scam=True).count(),
                "scams_last_7_days": EmailRecord.objects.filter(
                    is_scam=True, received_at__gte=last_7
                ).count(),
                "scams_last_30_days": EmailRecord.objects.filter(
                    is_scam=True, received_at__gte=last_30
                ).count(),
                "top_scam_senders": top_senders,
            }
        )


class ScanView(APIView):
    """POST /api/scan/ — trigger an on-demand Gmail scan synchronously."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from dashboard.scanner import run_scan

        try:
            result = run_scan()
            return Response(result)
        except Exception:
            logger.exception("Failed to run Gmail scan")
            return Response(
                {"error": "Scan failed. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
