from django.db import models


class EmailRecord(models.Model):
    """Stores the result of scanning one Gmail message through the ML model."""

    gmail_id = models.CharField(max_length=200, unique=True)
    sender = models.CharField(max_length=500)
    subject = models.CharField(max_length=1000)
    snippet = models.TextField()
    received_at = models.DateTimeField()
    # confidence: ML model output, 0.0 (definitely legit) – 1.0 (definitely scam)
    confidence = models.FloatField()
    is_scam = models.BooleanField()
    labeled_in_gmail = models.BooleanField(default=False)
    scanned_at = models.DateTimeField(auto_now_add=True)
    # reasons: rule-based tags explaining why the email was flagged as scam
    reasons = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-received_at"]
        indexes = [models.Index(fields=["is_scam", "received_at"])]

    def __str__(self) -> str:
        tag = "SCAM" if self.is_scam else "LEGIT"
        return f"{tag} | {self.subject[:60]}"


class ScanSettings(models.Model):
    """
    Singleton configuration row — always pk=1.

    Controls how far back to scan, how often to run automatically,
    and whether to send email summary reports.
    """

    NOTIFY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    scan_window_days = models.PositiveIntegerField(default=7)
    scan_frequency_hours = models.PositiveIntegerField(default=6)
    notify_frequency = models.CharField(
        max_length=10, choices=NOTIFY_CHOICES, default="weekly"
    )
    notify_via_email = models.BooleanField(default=False)
    notify_email_address = models.EmailField(blank=True)

    class Meta:
        verbose_name_plural = "Scan settings"

    def save(self, *args, **kwargs) -> None:
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "ScanSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return "Scan Settings"


class SummaryReport(models.Model):
    """A generated summary of scam activity for a given time period."""

    PERIOD_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    generated_at = models.DateTimeField(auto_now_add=True)
    total_scams = models.PositiveIntegerField()
    # top_senders: list of {"sender": "...", "count": N}, most frequent scam senders
    top_senders = models.JSONField(default=list)

    class Meta:
        ordering = ["-generated_at"]
        indexes = [models.Index(fields=["period", "generated_at"])]

    def __str__(self) -> str:
        return f"{self.period} report — {self.generated_at:%Y-%m-%d}"
