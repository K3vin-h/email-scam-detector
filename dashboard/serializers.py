from rest_framework import serializers

from dashboard.models import EmailRecord, ScanSettings, SummaryReport


class EmailRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailRecord
        fields = [
            "id",
            "gmail_id",
            "sender",
            "subject",
            "snippet",
            "received_at",
            "confidence",
            "is_scam",
            "labeled_in_gmail",
            "scanned_at",
        ]
        read_only_fields = fields


class ScanSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanSettings
        fields = [
            "scan_window_days",
            "scan_frequency_hours",
            "notify_frequency",
            "notify_via_email",
            "notify_email_address",
        ]


class SummaryReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummaryReport
        fields = ["id", "period", "generated_at", "total_scams", "top_senders"]
        read_only_fields = fields
