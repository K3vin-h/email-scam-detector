import logging
from datetime import date, timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dashboard.models import EmailRecord, ScanSettings, SummaryReport
from dashboard.reports import ensure_summary_reports
from dashboard.risk import RISK_LEVELS, RISK_SCAM, risk_level_for_email
from dashboard.serializers import (
    EmailRecordSerializer,
    ScanSettingsSerializer,
    SummaryReportSerializer,
)

logger = logging.getLogger(__name__)


class HealthView(APIView):
    """GET /api/health/ — health of the backend."""
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
        risk_level = self.request.query_params.get("risk_level")
        if is_scam is not None:
            value = is_scam.lower()
            if value not in ("true", "false"):
                raise ValidationError(
                    {"is_scam": "Expected 'true' or 'false'."}
                )
            qs = qs.filter(is_scam=value == "true")
        if risk_level is not None:
            if risk_level not in ("legit", "possible_scam", "scam"):
                raise ValidationError(
                    {"risk_level": "Expected 'legit', 'possible_scam', or 'scam'."}
                )
            ids = [
                record.id
                for record in qs
                if risk_level_for_email(
                    sender=record.sender,
                    confidence=record.confidence,
                    is_scam=record.is_scam,
                    user_risk_override=record.user_risk_override,
                ) == risk_level
            ]
            qs = qs.filter(id__in=ids)
        return qs


class ScanSettingsView(APIView):
    """GET/PATCH /api/settings/ — read or partially update the singleton settings row."""

    permission_classes = [IsAuthenticated]

    def _serialize_settings(self, settings):
        data = ScanSettingsSerializer(settings).data
        data.update(self._gmail_metadata())
        return data

    def _gmail_metadata(self):
        metadata = {
            "gmail_connected": False,
            "gmail_email_address": "",
            "gmail_last_sync": None,
        }

        try:
            from gmail.auth import get_service

            profile = get_service().users().getProfile(userId="me").execute()
        except Exception:
            logger.info("Gmail profile unavailable while loading settings", exc_info=True)
            return metadata

        latest_scan = (
            EmailRecord.objects.order_by("-scanned_at")
            .values_list("scanned_at", flat=True)
            .first()
        )

        metadata.update(
            {
                "gmail_connected": True,
                "gmail_email_address": profile.get("emailAddress", ""),
                "gmail_last_sync": latest_scan.isoformat() if latest_scan else None,
            }
        )
        return metadata

    def get(self, request):
        settings = ScanSettings.load()
        return Response(self._serialize_settings(settings))

    def patch(self, request):
        settings = ScanSettings.load()
        serializer = ScanSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self._serialize_settings(serializer.instance))


class SummaryReportListView(ListAPIView):
    """GET /api/reports/?period=daily|weekly|monthly — paginated report list."""

    permission_classes = [IsAuthenticated]
    serializer_class = SummaryReportSerializer

    def get_queryset(self):
        ensure_summary_reports()
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

        scam_ids = [
            record.id
            for record in EmailRecord.objects.all()
            if risk_level_for_email(
                    sender=record.sender,
                    confidence=record.confidence,
                    is_scam=record.is_scam,
                    user_risk_override=record.user_risk_override,
            ) == RISK_SCAM
        ]
        scam_qs = EmailRecord.objects.filter(id__in=scam_ids)

        top_senders = list(
            scam_qs
            .values("sender")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        return Response(
            {
                "total_scanned": EmailRecord.objects.count(),
                "total_scams": scam_qs.count(),
                "scams_last_7_days": scam_qs.filter(received_at__gte=last_7).count(),
                "scams_last_30_days": scam_qs.filter(received_at__gte=last_30).count(),
                "top_scam_senders": top_senders,
            }
        )


class DailyStatsView(APIView):
    """GET /api/stats/daily/ — scanned and scam counts for the last 7 days."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)

        rows = (
            EmailRecord.objects.filter(scanned_at__date__gte=seven_days_ago)
            .values("scanned_at__date")
            .annotate(
                scanned=Count("id"),
                scams=Count("id", filter=Q(id__in=[
                    record.id
                    for record in EmailRecord.objects.all()
                    if risk_level_for_email(
                        sender=record.sender,
                        confidence=record.confidence,
                        is_scam=record.is_scam,
                        user_risk_override=record.user_risk_override,
                    ) == RISK_SCAM
                ])),
            )
            .order_by("scanned_at__date")
        )

        # Build a full 7-day range with zeros for missing days
        data: list[dict] = []
        row_map = {r["scanned_at__date"]: r for r in rows}
        for i in range(7):
            d: date = seven_days_ago + timedelta(days=i)
            row = row_map.get(d, {})
            data.append(
                {
                    "day": d.strftime("%a"),
                    "date": d.isoformat(),
                    "scanned": row.get("scanned", 0),
                    "scams": row.get("scams", 0),
                }
            )

        return Response(data)


class TopSendersView(APIView):
    """GET /api/stats/senders/ — most impersonated domain, highest risk sender, scam trend."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from collections import Counter

        today = timezone.now().date()
        last_7 = today - timedelta(days=6)
        prior_7_start = today - timedelta(days=13)

        scam_ids = [
            record.id
            for record in EmailRecord.objects.all()
            if risk_level_for_email(
                sender=record.sender,
                confidence=record.confidence,
                is_scam=record.is_scam,
                user_risk_override=record.user_risk_override,
            ) == RISK_SCAM
        ]
        scam_qs = EmailRecord.objects.filter(id__in=scam_ids)

        top_email = (
            scam_qs.values("sender")
            .annotate(n=Count("id"))
            .order_by("-n")
            .first()
        )
        highest_risk = top_email["sender"] if top_email else None

        domains = [
            r["sender"].split("@")[-1]
            for r in scam_qs.values("sender")
        ]
        domain_counts = Counter(domains)
        most_impersonated = (
            domain_counts.most_common(1)[0][0] if domain_counts else None
        )

        c_last = scam_qs.filter(scanned_at__date__gte=last_7).count()
        c_prior = scam_qs.filter(
            scanned_at__date__gte=prior_7_start,
            scanned_at__date__lt=last_7,
        ).count()
        trend = round((c_last - c_prior) / max(c_prior, 1) * 100)

        return Response(
            {
                "most_impersonated": most_impersonated,
                "highest_risk_sender": highest_risk,
                "scam_trend_pct": trend,
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


class EmailRiskFeedbackView(APIView):
    """PATCH /api/emails/<id>/risk/ — manually correct an email risk tag."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        risk_level = request.data.get("risk_level")
        if risk_level not in RISK_LEVELS:
            return Response(
                {"risk_level": "Expected 'legit', 'possible_scam', or 'scam'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            record = EmailRecord.objects.get(pk=pk)
        except EmailRecord.DoesNotExist:
            return Response(
                {"detail": "Email not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        record.user_risk_override = risk_level
        record.save(update_fields=["user_risk_override"])
        SummaryReport.objects.all().delete()
        ensure_summary_reports()
        return Response(EmailRecordSerializer(record).data)
