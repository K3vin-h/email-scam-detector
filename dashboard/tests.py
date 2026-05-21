from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIClient
from sklearn.feature_extraction.text import TfidfVectorizer

from dashboard.models import EmailRecord, ScanSettings, SummaryReport
from dashboard.risk import RISK_LEGIT, RISK_POSSIBLE, RISK_SCAM, risk_level_for_email
from dashboard.scanner import run_scan
from gmail.fetch import list_email_ids as gmail_list_email_ids
from gmail.fetch import list_emails as gmail_list_emails
from gmail.auth import _get_frontend_origin, _get_oauth_redirect_origin
from ml.predict import is_scam_confidence
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
        self.assertEqual(SummaryReport.objects.count(), 3)
        self.assertEqual(
            SummaryReport.objects.get(period="daily").top_senders,
            [{"sender": "sender@example.com", "count": 1}],
        )
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
    def test_scan_does_not_retry_label_for_low_confidence_existing_scam(
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
            confidence=0.80,
            is_scam=True,
            labeled_in_gmail=False,
        )
        list_email_ids.return_value = ["gmail-1"]

        result = run_scan()

        self.assertEqual(result, {"scanned": 1, "new": 0, "scams_found": 0})
        record = EmailRecord.objects.get(gmail_id="gmail-1")
        self.assertFalse(record.labeled_in_gmail)
        get_email.assert_not_called()
        load_predictor.assert_not_called()
        get_or_create_label.assert_not_called()
        apply_label.assert_not_called()

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

    def test_email_list_filters_by_risk_level(self):
        self.client.force_authenticate(user=self.user)
        EmailRecord.objects.create(
            gmail_id="trusted",
            sender="Adobe Acrobat <mail@mail.adobe.com>",
            subject="Adobe update",
            snippet="Your document is ready",
            received_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
            confidence=0.99,
            is_scam=True,
            labeled_in_gmail=False,
        )
        EmailRecord.objects.create(
            gmail_id="possible",
            sender="notice@example.com",
            subject="Verify your account",
            snippet="Please review",
            received_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
            confidence=0.70,
            is_scam=False,
            labeled_in_gmail=False,
        )
        EmailRecord.objects.create(
            gmail_id="scam",
            sender="bad@example.com",
            subject="Claim prize",
            snippet="Act now",
            received_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
            confidence=0.95,
            is_scam=True,
            labeled_in_gmail=False,
        )

        legit_response = self.client.get("/api/emails/?risk_level=legit")
        possible_response = self.client.get("/api/emails/?risk_level=possible_scam")
        scam_response = self.client.get("/api/emails/?risk_level=scam")

        self.assertEqual(legit_response.status_code, 200)
        self.assertEqual(legit_response.json()["results"][0]["gmail_id"], "trusted")
        self.assertEqual(legit_response.json()["results"][0]["risk_label"], "Legit")
        self.assertEqual(possible_response.json()["results"][0]["gmail_id"], "possible")
        self.assertEqual(scam_response.json()["results"][0]["gmail_id"], "scam")

    def test_email_list_rejects_invalid_risk_level_filter(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/emails/?risk_level=maybe")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"risk_level": "Expected 'legit', 'possible_scam', or 'scam'."},
        )

    def test_email_risk_feedback_overrides_model_risk(self):
        self.client.force_authenticate(user=self.user)
        record = EmailRecord.objects.create(
            gmail_id="gmail-1",
            sender="bad@example.com",
            subject="False positive",
            snippet="Looks safe",
            received_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
            confidence=0.95,
            is_scam=True,
            labeled_in_gmail=False,
        )

        response = self.client.patch(
            f"/api/emails/{record.id}/risk/",
            {"risk_level": "legit"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.user_risk_override, "legit")
        self.assertEqual(response.json()["risk_level"], "legit")
        self.assertEqual(response.json()["risk_label"], "Legit")

    def test_email_risk_feedback_rejects_invalid_risk(self):
        self.client.force_authenticate(user=self.user)
        record = EmailRecord.objects.create(
            gmail_id="gmail-1",
            sender="bad@example.com",
            subject="Message",
            snippet="Snippet",
            received_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
            confidence=0.95,
            is_scam=True,
            labeled_in_gmail=False,
        )

        response = self.client.patch(
            f"/api/emails/{record.id}/risk/",
            {"risk_level": "wrong"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("risk_level", response.json())

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

    def test_reports_api_backfills_reports_from_existing_scan_results(self):
        self.client.force_authenticate(user=self.user)
        EmailRecord.objects.create(
            gmail_id="gmail-1",
            sender="scam@example.com",
            subject="Prize",
            snippet="Claim your prize",
            received_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
            confidence=0.95,
            is_scam=True,
            labeled_in_gmail=True,
        )

        response = self.client.get("/api/reports/?period=daily")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["period"], "daily")
        self.assertEqual(body["results"][0]["total_scams"], 1)
        self.assertEqual(
            body["results"][0]["top_senders"],
            [{"sender": "scam@example.com", "count": 1}],
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


class PredictorThresholdTests(TestCase):
    def test_mid_confidence_messages_are_not_marked_as_scam(self):
        self.assertFalse(is_scam_confidence(0.84))

    def test_high_confidence_messages_are_marked_as_scam(self):
        self.assertTrue(is_scam_confidence(0.85))


class SchedulerAutostartTests(TestCase):
    """Tests for dashboard.apps scheduler startup gating."""

    def test_management_commands_do_not_autostart_scheduler(self):
        from dashboard.apps import _should_start_scheduler

        with patch("dashboard.apps.sys.argv", ["manage.py", "migrate"]):
            with patch.dict("dashboard.apps.os.environ", {}, clear=True):
                self.assertFalse(_should_start_scheduler())

    def test_runserver_parent_reloader_does_not_autostart_scheduler(self):
        from dashboard.apps import _should_start_scheduler

        with patch("dashboard.apps.sys.argv", ["manage.py", "runserver"]):
            with patch.dict("dashboard.apps.os.environ", {}, clear=True):
                self.assertFalse(_should_start_scheduler())

    def test_runserver_child_autostarts_scheduler(self):
        from dashboard.apps import _should_start_scheduler

        with patch("dashboard.apps.sys.argv", ["manage.py", "runserver"]):
            with patch.dict("dashboard.apps.os.environ", {"RUN_MAIN": "true"}, clear=True):
                self.assertTrue(_should_start_scheduler())

    def test_env_flag_autostarts_scheduler(self):
        from dashboard.apps import SCHEDULER_AUTOSTART_ENV, _should_start_scheduler

        with patch("dashboard.apps.sys.argv", ["manage.py", "gunicorn"]):
            with patch.dict(
                "dashboard.apps.os.environ",
                {SCHEDULER_AUTOSTART_ENV: "true"},
                clear=True,
            ):
                self.assertTrue(_should_start_scheduler())


class SchedulerStartTests(TestCase):
    """Tests for dashboard.scheduler.start_scheduler()."""

    def setUp(self):
        # Reset the singleton before each test so tests are independent
        import dashboard.scheduler as mod
        mod.stop_scheduler(wait=False)
        mod._scheduler = None
        mod._current_interval_hours = None
        mod._current_notify_frequency = None

    def tearDown(self):
        # Clean up any real scheduler started during a test
        import dashboard.scheduler as mod
        try:
            mod.stop_scheduler(wait=False)
        except Exception:
            mod._scheduler = None

    @patch("dashboard.scheduler._acquire_process_lock", return_value=True)
    @patch("dashboard.scheduler.BackgroundScheduler")
    def test_start_scheduler_creates_and_starts_scheduler(self, MockScheduler, _mock_lock):
        from dashboard.scheduler import start_scheduler, get_scheduler

        start_scheduler(6)

        MockScheduler.assert_called_once_with(daemon=True)
        # scan job + settings_sync job + report job
        self.assertEqual(MockScheduler.return_value.add_job.call_count, 3)
        MockScheduler.return_value.start.assert_called_once()
        self.assertIsNotNone(get_scheduler())

    @patch("dashboard.scheduler._acquire_process_lock", return_value=True)
    @patch("dashboard.scheduler.BackgroundScheduler")
    def test_start_scheduler_idempotent(self, MockScheduler, _mock_lock):
        from dashboard.scheduler import start_scheduler

        start_scheduler(6)
        start_scheduler(12)  # Second call must be ignored

        # Only one Scheduler instance should be created
        MockScheduler.assert_called_once()

    @patch("dashboard.scheduler._acquire_process_lock")
    @patch("dashboard.scheduler.BackgroundScheduler")
    def test_start_scheduler_skips_when_another_process_owns_lock(
        self,
        MockScheduler,
        mock_acquire_process_lock,
    ):
        from dashboard.scheduler import start_scheduler, get_scheduler

        mock_acquire_process_lock.return_value = False

        start_scheduler(6)

        MockScheduler.assert_not_called()
        self.assertIsNone(get_scheduler())

    @patch("dashboard.scheduler._acquire_process_lock", return_value=True)
    @patch("dashboard.scheduler.BackgroundScheduler")
    def test_start_scheduler_uses_provided_interval(self, MockScheduler, _mock_lock):
        from dashboard.scheduler import start_scheduler, SCAN_JOB_ID

        start_scheduler(8)

        scan_call = MockScheduler.return_value.add_job.call_args_list[0]
        call_kwargs = scan_call[1]
        self.assertEqual(call_kwargs["id"], SCAN_JOB_ID)
        # Trigger should be an IntervalTrigger with 8-hour interval
        trigger = call_kwargs["trigger"]
        self.assertEqual(trigger.interval.total_seconds(), 8 * 3600)

    @patch("dashboard.scheduler._acquire_process_lock", return_value=True)
    @patch("dashboard.scheduler.BackgroundScheduler")
    def test_start_scheduler_adds_settings_sync_job(self, MockScheduler, _mock_lock):
        from dashboard.scheduler import (
            SETTINGS_SYNC_INTERVAL_SECONDS,
            SETTINGS_SYNC_JOB_ID,
            start_scheduler,
        )

        start_scheduler(6)

        sync_call = MockScheduler.return_value.add_job.call_args_list[1]
        call_kwargs = sync_call[1]
        self.assertEqual(call_kwargs["id"], SETTINGS_SYNC_JOB_ID)
        trigger = call_kwargs["trigger"]
        self.assertEqual(trigger.interval.total_seconds(), SETTINGS_SYNC_INTERVAL_SECONDS)


class RescheduleTests(TestCase):
    """Tests for dashboard.scheduler.reschedule_scan()."""

    def setUp(self):
        import dashboard.scheduler as mod
        mod.stop_scheduler(wait=False)
        mod._scheduler = None
        mod._current_interval_hours = None
        mod._current_notify_frequency = None

    def tearDown(self):
        import dashboard.scheduler as mod
        try:
            mod.stop_scheduler(wait=False)
        except Exception:
            mod._scheduler = None

    @patch("dashboard.scheduler._acquire_process_lock", return_value=True)
    @patch("dashboard.scheduler.BackgroundScheduler")
    def test_reschedule_updates_existing_job(self, MockScheduler, _mock_lock):
        from dashboard.scheduler import start_scheduler, reschedule_scan, SCAN_JOB_ID

        start_scheduler(6)
        reschedule_scan(12)

        MockScheduler.return_value.reschedule_job.assert_called_once()
        call_args = MockScheduler.return_value.reschedule_job.call_args
        self.assertEqual(call_args[0][0], SCAN_JOB_ID)
        new_trigger = call_args[1]["trigger"]
        self.assertEqual(new_trigger.interval.total_seconds(), 12 * 3600)

    @patch("dashboard.scheduler.reschedule_report_job")
    @patch("dashboard.scheduler.reschedule_scan")
    def test_settings_sync_reschedules_when_persisted_interval_changes(
        self,
        mock_reschedule,
        mock_report_reschedule,
    ):
        import dashboard.scheduler as mod

        ScanSettings.objects.update_or_create(pk=1, defaults={"scan_frequency_hours": 12})
        mock_reschedule.reset_mock()
        mod._scheduler = object()
        mod._current_interval_hours = 6
        # Freeze notify_frequency to match DB default so only scan reschedule fires
        mod._current_notify_frequency = "weekly"

        mod._sync_scan_settings()

        mock_reschedule.assert_called_once_with(12)
        mock_report_reschedule.assert_not_called()

    def test_reschedule_noop_when_scheduler_not_started(self):
        from dashboard.scheduler import reschedule_scan
        # Must not raise even though _scheduler is None
        reschedule_scan(12)


class BackgroundScanJobTests(TestCase):
    """Tests for dashboard.scheduler._run_scan_job()."""

    @patch("dashboard.scanner.run_scan")
    def test_run_scan_job_calls_run_scan(self, mock_run_scan):
        from dashboard.scheduler import _run_scan_job

        mock_run_scan.return_value = {"scanned": 5, "new": 2, "scams_found": 1}

        _run_scan_job()

        mock_run_scan.assert_called_once_with()

    @patch("dashboard.scanner.run_scan")
    def test_run_scan_job_swallows_exception(self, mock_run_scan):
        from dashboard.scheduler import _run_scan_job

        mock_run_scan.side_effect = RuntimeError("Gmail API down")

        # Exception must not propagate — scheduler thread must stay alive
        try:
            _run_scan_job()
        except RuntimeError:
            self.fail("_run_scan_job() should not propagate exceptions")


class SignalRescheduleTests(TestCase):
    """Tests that saving ScanSettings triggers a reschedule."""

    def setUp(self):
        import dashboard.scheduler as mod
        mod.stop_scheduler(wait=False)
        mod._scheduler = None
        mod._current_interval_hours = None
        mod._current_notify_frequency = None

    def tearDown(self):
        import dashboard.scheduler as mod
        try:
            mod.stop_scheduler(wait=False)
        except Exception:
            mod._scheduler = None

    @patch("dashboard.scheduler.reschedule_scan")
    def test_settings_save_triggers_reschedule(self, mock_reschedule):
        settings_obj = ScanSettings.load()
        # ScanSettings.load() saves the default row, firing the signal once.
        # Reset so we only assert on the explicit frequency change below.
        mock_reschedule.reset_mock()

        settings_obj.scan_frequency_hours = 12
        settings_obj.save()

        mock_reschedule.assert_called_once_with(12)


class RiskLevelTests(TestCase):
    def test_trusted_adobe_sender_is_legit_even_with_high_model_confidence(self):
        self.assertEqual(
            risk_level_for_email(
                sender="Adobe Acrobat <mail@mail.adobe.com>",
                confidence=0.99,
                is_scam=True,
            ),
            RISK_LEGIT,
        )

    def test_trusted_osu_sender_is_legit_even_with_high_model_confidence(self):
        self.assertEqual(
            risk_level_for_email(
                sender='"osu!" <osu@ppy.sh>',
                confidence=0.99,
                is_scam=True,
            ),
            RISK_LEGIT,
        )

    def test_medium_confidence_email_is_possible_scam(self):
        self.assertEqual(
            risk_level_for_email(
                sender="notice@example.com",
                confidence=0.65,
                is_scam=False,
            ),
            RISK_POSSIBLE,
        )

    def test_high_confidence_model_scam_is_scam(self):
        self.assertEqual(
            risk_level_for_email(
                sender="bad@example.com",
                confidence=0.95,
                is_scam=True,
            ),
            RISK_SCAM,
        )


class EmailReportTests(TestCase):
    """Tests for dashboard.email_report.send_summary_email()."""

    def _make_report(self, period="weekly", total_scams=5):
        return SummaryReport.objects.create(
            period=period,
            total_scams=total_scams,
            top_senders=[{"sender": "spam@bad.com", "count": 3}],
        )

    @patch("dashboard.email_report.EmailMultiAlternatives")
    def test_send_summary_email_sends_to_recipient(self, MockEmail):
        from dashboard.email_report import send_summary_email

        report = self._make_report()
        result = send_summary_email(report, "user@example.com")

        self.assertTrue(result)
        MockEmail.assert_called_once()
        _, kwargs = MockEmail.call_args
        self.assertEqual(kwargs["to"], ["user@example.com"])
        self.assertIn("Weekly", kwargs["subject"])

    @patch("dashboard.email_report.EmailMultiAlternatives")
    def test_send_summary_email_subject_matches_period(self, MockEmail):
        from dashboard.email_report import send_summary_email

        for period, label in [("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")]:
            MockEmail.reset_mock()
            report = self._make_report(period=period)
            send_summary_email(report, "user@example.com")
            _, kwargs = MockEmail.call_args
            self.assertIn(label, kwargs["subject"])

    @patch("dashboard.email_report.EmailMultiAlternatives")
    def test_send_summary_email_attaches_html_alternative(self, MockEmail):
        from dashboard.email_report import send_summary_email

        report = self._make_report()
        send_summary_email(report, "user@example.com")

        instance = MockEmail.return_value
        instance.attach_alternative.assert_called_once()
        _, attach_kwargs = instance.attach_alternative.call_args
        # Second positional arg is the mime type
        args = instance.attach_alternative.call_args[0]
        self.assertEqual(args[1], "text/html")

    @patch("dashboard.email_report.EmailMultiAlternatives")
    def test_send_summary_email_escapes_sender_in_html(self, MockEmail):
        from dashboard.email_report import _build_html_body

        report = self._make_report()
        report.top_senders = [{"sender": "<script>alert(1)</script>", "count": 1}]
        html = _build_html_body(report)

        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    @patch("dashboard.email_report.EmailMultiAlternatives")
    def test_send_summary_email_propagates_smtp_error(self, MockEmail):
        from dashboard.email_report import send_summary_email

        MockEmail.return_value.send.side_effect = Exception("SMTP connection refused")
        report = self._make_report()

        with self.assertRaises(Exception, msg="SMTP connection refused"):
            send_summary_email(report, "user@example.com")


class ReportJobTests(TestCase):
    """Tests for dashboard.scheduler._run_report_job()."""

    @patch("dashboard.reports.generate_summary_reports")
    def test_run_report_job_generates_reports(self, mock_generate):
        from dashboard.scheduler import _run_report_job

        ScanSettings.objects.update_or_create(
            pk=1,
            defaults={"notify_frequency": "weekly"},
        )
        mock_generate.return_value = []
        _run_report_job()

        mock_generate.assert_called_once_with(period="weekly")

    @patch("dashboard.email_report.send_summary_email")
    @patch("dashboard.reports.generate_summary_reports")
    def test_run_report_job_sends_email_when_enabled(self, mock_generate, mock_send):
        from dashboard.scheduler import _run_report_job

        ScanSettings.objects.update_or_create(
            pk=1,
            defaults={
                "notify_via_email": True,
                "notify_email_address": "user@example.com",
                "notify_frequency": "weekly",
            },
        )
        report = SummaryReport.objects.create(
            period="weekly", total_scams=3, top_senders=[]
        )
        mock_generate.return_value = [report]

        _run_report_job()

        mock_send.assert_called_once_with(report, "user@example.com")

    @patch("dashboard.email_report.send_summary_email")
    @patch("dashboard.reports.generate_summary_reports")
    def test_run_report_job_only_generates_matching_frequency(
        self,
        mock_generate,
        mock_send,
    ):
        from dashboard.scheduler import _run_report_job

        ScanSettings.objects.update_or_create(
            pk=1,
            defaults={
                "notify_via_email": True,
                "notify_email_address": "user@example.com",
                "notify_frequency": "daily",
            },
        )
        report = SummaryReport.objects.create(period="daily", total_scams=1, top_senders=[])
        mock_generate.return_value = [report]

        _run_report_job()

        mock_generate.assert_called_once_with(period="daily")
        mock_send.assert_called_once_with(report, "user@example.com")

    @patch("dashboard.email_report.send_summary_email")
    @patch("dashboard.reports.generate_summary_reports")
    def test_run_report_job_skips_email_when_disabled(self, mock_generate, mock_send):
        from dashboard.scheduler import _run_report_job

        ScanSettings.objects.update_or_create(
            pk=1, defaults={"notify_via_email": False, "notify_email_address": ""}
        )
        report = SummaryReport.objects.create(
            period="weekly", total_scams=3, top_senders=[]
        )
        mock_generate.return_value = [report]

        _run_report_job()

        mock_send.assert_not_called()

    @patch("dashboard.email_report.send_summary_email")
    @patch("dashboard.reports.generate_summary_reports")
    def test_run_report_job_only_emails_matching_frequency(self, mock_generate, mock_send):
        from dashboard.scheduler import _run_report_job

        ScanSettings.objects.update_or_create(
            pk=1,
            defaults={
                "notify_via_email": True,
                "notify_email_address": "user@example.com",
                "notify_frequency": "daily",
            },
        )
        daily = SummaryReport.objects.create(period="daily", total_scams=1, top_senders=[])
        weekly = SummaryReport.objects.create(period="weekly", total_scams=5, top_senders=[])
        mock_generate.return_value = [daily, weekly]

        _run_report_job()

        mock_generate.assert_called_once_with(period="daily")
        mock_send.assert_called_once_with(daily, "user@example.com")

    @patch("dashboard.reports.generate_summary_reports")
    def test_run_report_job_swallows_exception(self, mock_generate):
        from dashboard.scheduler import _run_report_job

        mock_generate.side_effect = RuntimeError("DB is down")

        try:
            _run_report_job()
        except RuntimeError:
            self.fail("_run_report_job() should not propagate exceptions")

    @patch("dashboard.scheduler._acquire_process_lock", return_value=True)
    @patch("dashboard.scheduler.BackgroundScheduler")
    def test_start_scheduler_adds_report_job(self, MockScheduler, _mock_lock):
        import dashboard.scheduler as mod
        mod.stop_scheduler(wait=False)
        mod._scheduler = None
        mod._current_interval_hours = None
        mod._current_notify_frequency = None

        from dashboard.scheduler import start_scheduler, REPORT_JOB_ID

        start_scheduler(6)

        job_ids = [call[1]["id"] for call in MockScheduler.return_value.add_job.call_args_list]
        self.assertIn(REPORT_JOB_ID, job_ids)

        mod.stop_scheduler(wait=False)

    @patch("dashboard.scheduler._acquire_process_lock", return_value=True)
    @patch("dashboard.scheduler.BackgroundScheduler")
    def test_reschedule_report_job_updates_trigger(self, MockScheduler, _mock_lock):
        import dashboard.scheduler as mod
        mod.stop_scheduler(wait=False)
        mod._scheduler = None
        mod._current_interval_hours = None
        mod._current_notify_frequency = None

        from dashboard.scheduler import start_scheduler, reschedule_report_job, REPORT_JOB_ID

        start_scheduler(6)
        reschedule_report_job("daily")

        MockScheduler.return_value.reschedule_job.assert_called_once()
        call_args = MockScheduler.return_value.reschedule_job.call_args
        self.assertEqual(call_args[0][0], REPORT_JOB_ID)
        trigger = call_args[1]["trigger"]
        self.assertEqual(trigger.interval.total_seconds(), 24 * 3600)

        mod.stop_scheduler(wait=False)


class GenerateReportCommandTests(TestCase):
    """Tests for dashboard.management.commands.generate_report."""

    @patch("dashboard.management.commands.generate_report.send_summary_email")
    @patch("dashboard.management.commands.generate_report.generate_summary_reports")
    def test_generate_report_only_generates_configured_frequency(
        self,
        mock_generate,
        mock_send,
    ):
        from django.core.management import call_command

        ScanSettings.objects.update_or_create(
            pk=1,
            defaults={
                "notify_frequency": "monthly",
                "notify_via_email": True,
                "notify_email_address": "user@example.com",
            },
        )
        report = SummaryReport.objects.create(
            period="monthly",
            total_scams=2,
            top_senders=[],
        )
        mock_generate.return_value = [report]

        call_command("generate_report")

        mock_generate.assert_called_once_with(period="monthly")
        mock_send.assert_called_once_with(report, "user@example.com")
