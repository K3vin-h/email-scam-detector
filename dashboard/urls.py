from django.urls import path

from dashboard.views import (
    EmailListView,
    HealthView,
    ScanSettingsView,
    ScanView,
    StatsView,
    SummaryReportListView,
)

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("emails/", EmailListView.as_view(), name="email-list"),
    path("settings/", ScanSettingsView.as_view(), name="scan-settings"),
    path("reports/", SummaryReportListView.as_view(), name="report-list"),
    path("stats/", StatsView.as_view(), name="stats"),
    path("scan/", ScanView.as_view(), name="scan"),
]
