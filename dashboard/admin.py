from django.contrib import admin

from dashboard.models import EmailRecord, ScanSettings, SummaryReport


@admin.register(EmailRecord)
class EmailRecordAdmin(admin.ModelAdmin):
    list_display = ["subject", "sender", "is_scam", "confidence", "received_at", "labeled_in_gmail"]
    list_filter = ["is_scam", "labeled_in_gmail"]
    search_fields = ["subject", "sender", "snippet"]
    readonly_fields = ["gmail_id", "scanned_at"]
    ordering = ["-received_at"]


@admin.register(ScanSettings)
class ScanSettingsAdmin(admin.ModelAdmin):
    # Prevent adding a second row — there can only be one settings object.
    def has_add_permission(self, request):
        return not ScanSettings.objects.exists()


@admin.register(SummaryReport)
class SummaryReportAdmin(admin.ModelAdmin):
    list_display = ["period", "generated_at", "total_scams"]
    list_filter = ["period"]
    readonly_fields = ["generated_at"]
