from rest_framework import serializers

from dashboard.models import EmailRecord, ScanSettings, SummaryReport
from dashboard.risk import risk_label, risk_level_for_email


class EmailRecordSerializer(serializers.ModelSerializer):
    risk_level = serializers.SerializerMethodField()
    risk_label = serializers.SerializerMethodField()

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
            "reasons",
            "user_risk_override",
            "risk_level",
            "risk_label",
        ]
        read_only_fields = fields

    def get_risk_level(self, obj):
        return risk_level_for_email(
            sender=obj.sender,
            confidence=obj.confidence,
            is_scam=obj.is_scam,
            user_risk_override=obj.user_risk_override,
        )

    def get_risk_label(self, obj):
        return risk_label(self.get_risk_level(obj))


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
