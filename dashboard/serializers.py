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

    def validate_scan_window_days(self, value):
        if not 1 <= value <= 365:
            raise serializers.ValidationError("Must be between 1 and 365 days.")
        return value

    def validate_scan_frequency_hours(self, value):
        if not 1 <= value <= 168:
            raise serializers.ValidationError("Must be between 1 and 168 hours.")
        return value

    def validate(self, attrs):
        notify_via_email = attrs.get(
            "notify_via_email",
            getattr(self.instance, "notify_via_email", False),
        )
        notify_email_address = attrs.get(
            "notify_email_address",
            getattr(self.instance, "notify_email_address", ""),
        )

        if notify_via_email and not notify_email_address:
            raise serializers.ValidationError(
                {
                    "notify_email_address": (
                        "This field is required when email notifications are enabled."
                    )
                }
            )

        return attrs


class SummaryReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SummaryReport
        fields = ["id", "period", "generated_at", "total_scams", "top_senders"]
        read_only_fields = fields
