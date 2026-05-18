from datetime import datetime, timezone
from unittest.mock import patch

from django.test import TestCase

from dashboard.models import EmailRecord
from dashboard.scanner import run_scan


class RunScanTests(TestCase):
    @patch("dashboard.scanner.apply_label")
    @patch("dashboard.scanner.get_or_create_label")
    @patch("dashboard.scanner.predict")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_emails")
    def test_dry_run_classifies_without_persisting_or_labeling(
        self,
        list_emails,
        get_email,
        predict,
        get_or_create_label,
        apply_label,
    ):
        list_emails.return_value = [{"id": "gmail-1"}]
        get_email.return_value = {
            "sender": "sender@example.com",
            "subject": "Prize",
            "snippet": "Click here",
            "body": "Claim your prize now",
            "received_at": datetime(2026, 5, 17, tzinfo=timezone.utc),
        }
        predict.return_value = (True, 0.95)

        result = run_scan(dry_run=True)

        self.assertEqual(result, {"scanned": 1, "new": 1, "scams_found": 1})
        self.assertEqual(EmailRecord.objects.count(), 0)
        get_or_create_label.assert_not_called()
        apply_label.assert_not_called()

    @patch("dashboard.scanner.apply_label")
    @patch("dashboard.scanner.get_or_create_label")
    @patch("dashboard.scanner.predict")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_emails")
    def test_scan_persists_and_labels_scam_email(
        self,
        list_emails,
        get_email,
        predict,
        get_or_create_label,
        apply_label,
    ):
        list_emails.return_value = [{"id": "gmail-1"}]
        get_email.return_value = {
            "sender": "sender@example.com",
            "subject": "Prize",
            "snippet": "Click here",
            "body": "Claim your prize now",
            "received_at": datetime(2026, 5, 17, tzinfo=timezone.utc),
        }
        predict.return_value = (True, 0.95)
        get_or_create_label.return_value = "Label_123"

        result = run_scan()

        self.assertEqual(result, {"scanned": 1, "new": 1, "scams_found": 1})
        record = EmailRecord.objects.get(gmail_id="gmail-1")
        self.assertTrue(record.is_scam)
        self.assertTrue(record.labeled_in_gmail)
        get_or_create_label.assert_called_once_with("Scam")
        apply_label.assert_called_once_with("gmail-1", "Label_123")
