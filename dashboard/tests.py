from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIClient
from sklearn.feature_extraction.text import TfidfVectorizer

from dashboard.models import EmailRecord, ScanSettings
from dashboard.scanner import run_scan
from gmail.fetch import list_email_ids as gmail_list_email_ids
from gmail.fetch import list_emails as gmail_list_emails
from gmail.auth import _get_frontend_origin, _get_oauth_redirect_origin
from ml.vectorizer_io import load_vectorizer, save_vectorizer


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
    @patch("dashboard.scanner.list_email_ids")
    def test_dry_run_classifies_without_persisting_or_labeling(
        self,
        list_email_ids,
        get_email,
        load_predictor,
        get_or_create_label,
        apply_label,
    ):
        list_email_ids.return_value = ["gmail-1"]
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
        list_email_ids.assert_called_once_with(max_results=None, query="after:2026/05/11")
        load_predictor.assert_called_once_with()
        predict.assert_called_once_with("Claim your prize now")
        get_or_create_label.assert_not_called()
        apply_label.assert_not_called()

    @patch("dashboard.scanner.apply_label")
    @patch("dashboard.scanner.get_or_create_label")
    @patch("dashboard.scanner.load_predictor")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_email_ids")
    def test_scan_persists_and_labels_scam_email(
        self,
        list_email_ids,
        get_email,
        load_predictor,
        get_or_create_label,
        apply_label,
    ):
        list_email_ids.return_value = ["gmail-1"]
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
    @patch("dashboard.scanner.list_email_ids")
    def test_scan_skips_existing_legitimate_record_without_fetching(
        self,
        list_email_ids,
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
            is_scam=False,
            labeled_in_gmail=False,
        )
        list_email_ids.return_value = ["gmail-1"]

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
    @patch("dashboard.scanner.list_email_ids")
    def test_scan_retries_label_for_existing_unlabeled_scam(
        self,
        list_email_ids,
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
        list_email_ids.return_value = ["gmail-1"]
        get_or_create_label.return_value = "Label_123"

        result = run_scan()

        self.assertEqual(result, {"scanned": 1, "new": 0, "scams_found": 0})
        record = EmailRecord.objects.get(gmail_id="gmail-1")
        self.assertTrue(record.labeled_in_gmail)
        get_email.assert_not_called()
        load_predictor.assert_not_called()
        get_or_create_label.assert_called_once_with("Scam")
        apply_label.assert_called_once_with("gmail-1", "Label_123")

    @patch("dashboard.scanner.apply_label")
    @patch("dashboard.scanner.get_or_create_label")
    @patch("dashboard.scanner.load_predictor")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_email_ids")
    def test_dry_run_skips_existing_record_without_counting_or_classifying(
        self,
        list_email_ids,
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
        list_email_ids.return_value = ["gmail-1"]

        result = run_scan(dry_run=True)

        self.assertEqual(result, {"scanned": 1, "new": 0, "scams_found": 0})
        self.assertEqual(EmailRecord.objects.count(), 1)
        get_email.assert_not_called()
        load_predictor.assert_not_called()
        get_or_create_label.assert_not_called()
        apply_label.assert_not_called()

    @patch("dashboard.scanner.load_predictor")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_email_ids")
    def test_scan_skips_messages_older_than_scan_window(
        self,
        list_email_ids,
        get_email,
        load_predictor,
    ):
        list_email_ids.return_value = ["old-gmail-1"]
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

    @patch("dashboard.scanner.apply_label")
    @patch("dashboard.scanner.get_or_create_label")
    @patch("dashboard.scanner.load_predictor")
    @patch("dashboard.scanner.get_email")
    @patch("dashboard.scanner.list_email_ids")
    def test_scan_bulk_skips_known_records_before_fetching(
        self,
        list_email_ids,
        get_email,
        load_predictor,
        get_or_create_label,
        apply_label,
    ):
        EmailRecord.objects.create(
            gmail_id="known-legit",
            sender="sender@example.com",
            subject="Already scanned",
            snippet="Existing snippet",
            received_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
            confidence=0.05,
            is_scam=False,
            labeled_in_gmail=False,
        )
        list_email_ids.return_value = ["known-legit", "new-scam"]
        get_email.return_value = {
            "sender": "sender@example.com",
            "subject": "Prize",
            "snippet": "Click here",
            "body": "Claim your prize now",
            "received_at": datetime(2026, 5, 17, tzinfo=timezone.utc),
        }
        load_predictor.return_value.return_value = (True, 0.95)
        get_or_create_label.return_value = "Label_123"

        result = run_scan()

        self.assertEqual(result, {"scanned": 2, "new": 1, "scams_found": 1})
        get_email.assert_called_once_with("new-scam")
        load_predictor.assert_called_once_with()
        apply_label.assert_called_once_with("new-scam", "Label_123")


class DashboardAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="tester",
        )

    def test_sensitive_dashboard_apis_require_authentication(self):
        endpoints = [
            ("get", "/api/emails/"),
            ("get", "/api/stats/"),
            ("get", "/api/settings/"),
            ("patch", "/api/settings/"),
            ("get", "/api/reports/"),
            ("post", "/api/scan/"),
        ]

        for method, path in endpoints:
            response = getattr(self.client, method)(path, {}, format="json")

            self.assertIn(response.status_code, (401, 403), path)

    def test_health_api_is_public(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_gmail_oauth_endpoints_require_authentication(self):
        endpoints = ["/auth/gmail/", "/auth/callback/"]

        for path in endpoints:
            response = self.client.get(path)

            self.assertEqual(response.status_code, 302, path)
            self.assertIn("/accounts/login/", response["Location"])

    def test_email_list_rejects_invalid_is_scam_filter(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/emails/?is_scam=maybe")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"is_scam": "Expected 'true' or 'false'."})

    def test_scan_settings_validation_rejects_unsafe_values(self):
        self.client.force_authenticate(user=self.user)
        ScanSettings.load()

        response = self.client.patch(
            "/api/settings/",
            {
                "scan_window_days": 0,
                "scan_frequency_hours": 999,
                "notify_via_email": True,
                "notify_email_address": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIn("scan_window_days", body)
        self.assertIn("scan_frequency_hours", body)

    def test_scan_settings_requires_email_when_notifications_enabled(self):
        self.client.force_authenticate(user=self.user)
        ScanSettings.load()

        response = self.client.patch(
            "/api/settings/",
            {
                "notify_via_email": True,
                "notify_email_address": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIn("notify_email_address", body)

    def test_scan_failure_returns_generic_error_to_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        with (
            self.assertLogs("dashboard.views", level="ERROR"),
            patch("dashboard.scanner.run_scan", side_effect=RuntimeError("secret details")),
        ):
            response = self.client.post("/api/scan/")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {"error": "Scan failed. Please try again later."},
        )


class GmailFetchTests(TestCase):
    def test_list_email_ids_fetches_all_pages_when_max_results_is_none(self):
        service = MagicMock()
        messages = service.users.return_value.messages.return_value
        messages.list.return_value.execute.side_effect = [
            {"messages": [{"id": "gmail-1"}], "nextPageToken": "page-2"},
            {"messages": [{"id": "gmail-2"}]},
        ]

        with patch("gmail.fetch.get_service", return_value=service):
            email_ids = gmail_list_email_ids(max_results=None, query="after:2026/05/11")

        self.assertEqual(email_ids, ["gmail-1", "gmail-2"])
        self.assertEqual(messages.list.call_count, 2)
        messages.get.assert_not_called()

    def test_list_emails_fetches_all_pages_when_max_results_is_none(self):
        service = MagicMock()
        messages = service.users.return_value.messages.return_value
        messages.list.return_value.execute.side_effect = [
            {"messages": [{"id": "gmail-1"}], "nextPageToken": "page-2"},
            {"messages": [{"id": "gmail-2"}]},
        ]
        messages.get.return_value.execute.side_effect = [
            {
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "First"},
                        {"name": "From", "value": "first@example.com"},
                    ]
                },
                "snippet": "First snippet",
            },
            {
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Second"},
                        {"name": "From", "value": "second@example.com"},
                    ]
                },
                "snippet": "Second snippet",
            },
        ]

        with patch("gmail.fetch.get_service", return_value=service):
            emails = gmail_list_emails(max_results=None, query="after:2026/05/11")

        self.assertEqual([email["id"] for email in emails], ["gmail-1", "gmail-2"])
        self.assertEqual(messages.list.call_count, 2)
        self.assertEqual(
            messages.list.call_args_list[0].kwargs,
            {
                "userId": "me",
                "maxResults": 50,
                "q": "after:2026/05/11",
                "pageToken": None,
            },
        )
        self.assertEqual(
            messages.list.call_args_list[1].kwargs,
            {
                "userId": "me",
                "maxResults": 50,
                "q": "after:2026/05/11",
                "pageToken": "page-2",
            },
        )


class GmailOAuthOriginTests(TestCase):
    @override_settings(
        CORS_ALLOWED_ORIGINS=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        FRONTEND_ORIGIN="http://localhost:5173",
    )
    def test_frontend_origin_preserves_active_loopback_host(self):
        request = RequestFactory().get(
            "/auth/gmail/",
            HTTP_HOST="127.0.0.1:5173",
        )

        self.assertEqual(_get_frontend_origin(request), "http://127.0.0.1:5173")

    @override_settings(
        CORS_ALLOWED_ORIGINS=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        FRONTEND_ORIGIN="http://localhost:5173",
    )
    def test_frontend_origin_uses_trusted_referer_before_default(self):
        request = RequestFactory().get(
            "/auth/gmail/",
            HTTP_REFERER="http://127.0.0.1:5173/settings",
        )

        self.assertEqual(_get_frontend_origin(request), "http://127.0.0.1:5173")

    @override_settings(
        CORS_ALLOWED_ORIGINS=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        FRONTEND_ORIGIN="http://localhost:5173",
    )
    def test_oauth_redirect_origin_uses_saved_trusted_origin(self):
        request = RequestFactory().get("/auth/callback/")
        request.session = {"oauth_frontend_origin": "http://127.0.0.1:5173"}

        self.assertEqual(_get_oauth_redirect_origin(request), "http://127.0.0.1:5173")

    @override_settings(
        CORS_ALLOWED_ORIGINS=["http://localhost:5173"],
        FRONTEND_ORIGIN="http://localhost:5173",
    )
    def test_oauth_redirect_origin_rejects_untrusted_saved_origin(self):
        request = RequestFactory().get("/auth/callback/")
        request.session = {"oauth_frontend_origin": "https://evil.example"}

        self.assertEqual(_get_oauth_redirect_origin(request), "http://localhost:5173")


class VectorizerIOTests(TestCase):
    def test_vectorizer_round_trips_without_pickle(self):
        vectorizer = TfidfVectorizer(max_features=10, sublinear_tf=True)
        vectorizer.fit(["claim your prize now", "meeting moved tomorrow"])

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "vectorizer.json"
            save_vectorizer(vectorizer, path)
            loaded = load_vectorizer(path)

        expected = vectorizer.transform(["claim prize"]).toarray()
        actual = loaded.transform(["claim prize"]).toarray()
        self.assertEqual(loaded.vocabulary_, vectorizer.vocabulary_)
        self.assertTrue((expected == actual).all())

    def test_vectorizer_load_fails_cleanly_for_missing_artifact(self):
        with self.assertRaisesRegex(RuntimeError, "Vectorizer artifact not found"):
            load_vectorizer(Path("missing-vectorizer.json"))
