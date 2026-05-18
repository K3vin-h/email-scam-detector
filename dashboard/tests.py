from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from django.test import TestCase

from dashboard.models import EmailRecord
from dashboard.scanner import run_scan


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 5, 18, tzinfo=tz)


class RunScanTests(TestCase):
    @patch("dashboard.scanner.datetime", FixedDateTime)
    @patch("dashboard.scanner.apply_label")
    @patch("dashboard.scanner.get_or_create_label")
    @patch("dashboard.scanner.load_predictor")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_emails")
    def test_dry_run_classifies_without_persisting_or_labeling(
        self,
        list_emails,
        get_email,
        load_predictor,
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
        predict = load_predictor.return_value
        predict.return_value = (True, 0.95)

        result = run_scan(dry_run=True)

        self.assertEqual(result, {"scanned": 1, "new": 1, "scams_found": 1})
        self.assertEqual(EmailRecord.objects.count(), 0)
        list_emails.assert_called_once_with(max_results=50, query="after:2026/05/11")
        load_predictor.assert_called_once_with()
        predict.assert_called_once_with("Claim your prize now")
        get_or_create_label.assert_not_called()
        apply_label.assert_not_called()

    @patch("dashboard.scanner.apply_label")
    @patch("dashboard.scanner.get_or_create_label")
    @patch("dashboard.scanner.load_predictor")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_emails")
    def test_scan_persists_and_labels_scam_email(
        self,
        list_emails,
        get_email,
        load_predictor,
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
        predict = load_predictor.return_value
        predict.return_value = (True, 0.95)
        get_or_create_label.return_value = "Label_123"

        result = run_scan()

        self.assertEqual(result, {"scanned": 1, "new": 1, "scams_found": 1})
        record = EmailRecord.objects.get(gmail_id="gmail-1")
        self.assertTrue(record.is_scam)
        self.assertTrue(record.labeled_in_gmail)
        get_or_create_label.assert_called_once_with("Scam")
        apply_label.assert_called_once_with("gmail-1", "Label_123")

    @patch("dashboard.scanner.apply_label")
    @patch("dashboard.scanner.get_or_create_label")
    @patch("dashboard.scanner.load_predictor")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_emails")
    def test_scan_skips_existing_record_without_labeling(
        self,
        list_emails,
        get_email,
        load_predictor,
        get_or_create_label,
        apply_label,
    ):
        EmailRecord.objects.create(
            gmail_id="gmail-1",
            sender="sender@example.com",
            subject="Already scanned",
            snippet="Existing snippet",
            received_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
            confidence=0.95,
            is_scam=True,
            labeled_in_gmail=False,
        )
        list_emails.return_value = [{"id": "gmail-1"}]

        result = run_scan()

        self.assertEqual(result, {"scanned": 1, "new": 0, "scams_found": 0})
        self.assertEqual(EmailRecord.objects.count(), 1)
        get_email.assert_not_called()
        load_predictor.assert_not_called()
        get_or_create_label.assert_not_called()
        apply_label.assert_not_called()

    @patch("dashboard.scanner.apply_label")
    @patch("dashboard.scanner.get_or_create_label")
    @patch("dashboard.scanner.load_predictor")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_emails")
    def test_dry_run_skips_existing_record_without_counting_or_classifying(
        self,
        list_emails,
        get_email,
        load_predictor,
        get_or_create_label,
        apply_label,
    ):
        EmailRecord.objects.create(
            gmail_id="gmail-1",
            sender="sender@example.com",
            subject="Already scanned",
            snippet="Existing snippet",
            received_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
            confidence=0.95,
            is_scam=True,
            labeled_in_gmail=True,
        )
        list_emails.return_value = [{"id": "gmail-1"}]

        result = run_scan(dry_run=True)

        self.assertEqual(result, {"scanned": 1, "new": 0, "scams_found": 0})
        self.assertEqual(EmailRecord.objects.count(), 1)
        get_email.assert_not_called()
        load_predictor.assert_not_called()
        get_or_create_label.assert_not_called()
        apply_label.assert_not_called()

    @patch("dashboard.scanner.load_predictor")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_emails")
    def test_scan_skips_messages_older_than_scan_window(
        self,
        list_emails,
        get_email,
        load_predictor,
    ):
        list_emails.return_value = [{"id": "old-gmail-1"}]
        get_email.return_value = {
            "sender": "sender@example.com",
            "subject": "Old message",
            "snippet": "Old snippet",
            "body": "Old body",
            "received_at": datetime.now(timezone.utc) - timedelta(days=8),
        }

        result = run_scan()

        self.assertEqual(result, {"scanned": 1, "new": 0, "scams_found": 0})
        self.assertEqual(EmailRecord.objects.count(), 0)
        load_predictor.assert_not_called()
