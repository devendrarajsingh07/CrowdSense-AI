import asyncio
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import (
    MAX_UPLOAD_BYTES,
    UPLOAD_DIR,
    UploadSizeLimitMiddleware,
    app,
)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_dashboard_and_offline_status_are_served(self):
        dashboard = self.client.get("/dashboard/")
        crowd = self.client.get("/crowd")

        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("CrowdSense AI", dashboard.text)
        self.assertEqual(crowd.status_code, 200)
        self.assertEqual(crowd.json()["camera"], "OFFLINE")

    def test_upload_uses_uuid_path_and_cleans_it_up(self):
        successful_result = {
            "success": True,
            "max_people": 2,
            "average_people": 1.5,
            "high_risk_events": 0,
        }

        with patch("backend.main.analyze_video", return_value=successful_result) as analyzer:
            response = self.client.post(
                "/analyze-video",
                files={"file": ("../../crowd_data.mp4", b"video-bytes", "video/mp4")},
            )

        analyzed_path = Path(analyzer.call_args.args[0])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(analyzed_path.parent, UPLOAD_DIR.resolve())
        self.assertNotIn("crowd_data", analyzed_path.name)
        self.assertFalse(analyzed_path.exists())

    def test_unsupported_upload_returns_http_error(self):
        response = self.client.post(
            "/analyze-video",
            files={"file": ("payload.py", b"print('bad')", "text/x-python")},
        )

        self.assertEqual(response.status_code, 415)
        self.assertIn("Unsupported video type", response.json()["detail"])

    def test_analyzer_failure_returns_422(self):
        with patch(
            "backend.main.analyze_video",
            return_value={"success": False, "error": "Unreadable video"},
        ):
            response = self.client.post(
                "/analyze-video",
                files={"file": ("broken.mp4", b"not-a-video", "video/mp4")},
            )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], "Unreadable video")

    def test_declared_oversized_upload_is_rejected_before_analysis(self):
        response = self.client.post(
            "/analyze-video",
            content=b"ignored",
            headers={"content-length": str(MAX_UPLOAD_BYTES + 2 * 1024 * 1024)},
        )

        self.assertEqual(response.status_code, 413)

    def test_chunked_oversized_upload_is_rejected(self):
        sent_messages = []
        request_messages = iter(
            [
                {"type": "http.request", "body": b"123", "more_body": True},
                {"type": "http.request", "body": b"456", "more_body": False},
            ]
        )

        async def receive():
            return next(request_messages)

        async def send(message):
            sent_messages.append(message)

        async def drain_body(_scope, receive_body, _send):
            while True:
                message = await receive_body()
                if not message.get("more_body"):
                    break

        middleware = UploadSizeLimitMiddleware(drain_body, max_request_bytes=5)
        scope = {"type": "http", "path": "/analyze-video", "headers": []}

        asyncio.run(middleware(scope, receive, send))

        self.assertEqual(sent_messages[0]["status"], 413)

    def test_report_is_a_pdf(self):
        response = self.client.get("/generate-report")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
