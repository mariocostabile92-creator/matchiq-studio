import asyncio
import json
import os
from io import BytesIO
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch
from PIL import Image


os.environ["SESSION_COOKIE_SECURE"] = "false"
os.environ["CORS_ALLOWED_ORIGINS"] = "https://studio.matchiq.it.com,http://127.0.0.1:8000,http://localhost:8000"
os.environ["ALLOWED_HOSTS"] = "studio.matchiq.it.com,127.0.0.1,localhost,test-server,testserver"

from backend.app.core import config


_TEST_STORAGE = tempfile.TemporaryDirectory(prefix="matchiq-auth-tests-")
config.STORAGE_DIR = Path(_TEST_STORAGE.name)

from backend.app.main import app  # noqa: E402
from backend.app.render import reel_renderer  # noqa: E402
from backend.app.routers import auth, media, reels  # noqa: E402

media.UPLOADS_DIR = config.STORAGE_DIR / "uploads"
media.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class ASGITestClient:
    """Small stdlib ASGI client; exercises the real FastAPI app and auth DB."""

    def __init__(self):
        self.cookies = {}

    def request(self, method, url, json_body=None, headers=None, body=None, omit_origin=False):
        parsed = urlsplit(url)
        request_headers = {key.lower(): value for key, value in (headers or {}).items()}
        request_headers = {key: value for key, value in request_headers.items() if value is not None}
        request_headers.setdefault("host", "test-server")
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            request_headers.setdefault("content-type", "application/json")
        body = body or b""
        if "cookie" not in request_headers and self.cookies:
            request_headers["cookie"] = "; ".join(f"{name}={value}" for name, value in self.cookies.items())
        if (
            not omit_origin
            and method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
            and "matchiq_session" in self.cookies
        ):
            request_headers.setdefault("origin", "http://127.0.0.1:8000")
        raw_headers = [(key.encode("latin-1"), value.encode("latin-1")) for key, value in request_headers.items()]
        messages = []
        received = False

        async def receive():
            nonlocal received
            if received:
                return {"type": "http.disconnect"}
            received = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            messages.append(message)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": "http",
            "path": parsed.path,
            "raw_path": parsed.path.encode("ascii"),
            "query_string": parsed.query.encode("ascii"),
            "root_path": "",
            "headers": raw_headers,
            "client": ("test-client", 50000),
            "server": ("test-server", 80),
            "state": {},
        }
        asyncio.run(app(scope, receive, send))
        start = next(message for message in messages if message["type"] == "http.response.start")
        response_body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
        response_headers = [(key.decode("latin-1").lower(), value.decode("latin-1")) for key, value in start["headers"]]
        for key, value in response_headers:
            if key != "set-cookie":
                continue
            cookie = SimpleCookie()
            cookie.load(value)
            for name, morsel in cookie.items():
                if morsel["max-age"] == "0" or not morsel.value:
                    self.cookies.pop(name, None)
                else:
                    self.cookies[name] = morsel.value
        content_type = next((value for key, value in response_headers if key == "content-type"), "")
        if response_body and "application/json" in content_type:
            data = json.loads(response_body)
        else:
            data = response_body or None
        return start["status"], response_headers, data


def tiny_png():
    output = BytesIO()
    Image.new("RGBA", (1, 1), (20, 80, 120, 255)).save(output, format="PNG")
    return output.getvalue()


class CentralAuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registrar = ASGITestClient()
        for name, email in (("User A", "user-a@example.test"), ("User B", "user-b@example.test")):
            status, _, data = cls.registrar.request(
                "POST", "/api/auth/register",
                json_body={"name": name, "email": email, "password": "strong-test-password"},
            )
            if status != 200 or not data.get("success"):
                raise AssertionError(f"Test account registration failed: {status} {data}")

    def setUp(self):
        self.user_a = self._login("user-a@example.test")
        self.user_b = self._login("user-b@example.test")

    def _login(self, email):
        client = ASGITestClient()
        status, headers, data = client.request(
            "POST", "/api/auth/login",
            json_body={"email": email, "password": "strong-test-password"},
        )
        self.assertEqual(status, 200, data)
        self.assertTrue(data["success"])
        self.assertIn("matchiq_session", client.cookies)
        cookie_headers = [value for key, value in headers if key == "set-cookie"]
        self.assertTrue(any("HttpOnly" in value for value in cookie_headers))
        return client

    def test_real_login_and_current_user(self):
        status, _, data = self.user_a.request("GET", "/api/auth/me")
        self.assertEqual(status, 200)
        self.assertEqual(data["user"]["email"], "user-a@example.test")

    def test_private_api_rejects_missing_and_invalid_session(self):
        protected_requests = [
            ("GET", "/api/auth/me", None),
            ("GET", "/api/projects", None),
            ("GET", "/api/campaigns", None),
            ("GET", "/api/media", None),
            ("POST", "/api/projects", {}),
            ("POST", "/api/campaigns", {}),
            ("PUT", "/api/projects/not-a-project", {}),
            ("PUT", "/api/campaigns/not-a-campaign", {}),
            ("GET", "/api/reels/status/not-a-job", None),
            ("POST", "/api/reels/storyboard", {}),
            ("POST", "/api/reels/generate-hooks", {}),
            ("POST", "/api/reels/create", {}),
            ("POST", "/api/reels/render-storyboard", {"storyboard": {
                "brand_name": "Test", "topic": "Test", "hook": "Hook",
                "creative_direction": "", "music_mood": "", "rhythm": "", "scenes": [],
            }}),
            ("POST", "/api/reels/regenerate-scene", {"scene": {
                "index": 1, "title": "Test", "visual": "Test", "camera": "Static",
                "motion": "None", "lighting": "Neutral", "voice_over": "Test", "subtitle": "Test",
            }}),
        ]
        anonymous = ASGITestClient()
        invalid = ASGITestClient()
        invalid.cookies["matchiq_session"] = "not-a-real-session"
        for method, path, payload in protected_requests:
            with self.subTest(path=path, session="missing"):
                self.assertEqual(anonymous.request(method, path, json_body=payload)[0], 401)
            with self.subTest(path=path, session="invalid"):
                self.assertEqual(invalid.request(method, path, json_body=payload)[0], 401)

    def test_expired_and_orphan_sessions_are_rejected(self):
        user = auth._get_user_by_email("user-a@example.test")
        expired_token = "expired-session-token"
        orphan_token = "orphan-session-token"
        expired_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        valid_until = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        with auth._connect() as conn:
            conn.execute(
                f"INSERT INTO sessions (token,user_id,created_at,expires_at) VALUES ({auth._param()},{auth._param()},{auth._param()},{auth._param()})",
                (expired_token, user["id"], auth._now(), expired_at),
            )
        raw = sqlite3.connect(auth.SQLITE_PATH)
        try:
            raw.execute("PRAGMA foreign_keys=OFF")
            raw.execute(
                "INSERT INTO sessions (token,user_id,created_at,expires_at) VALUES (?,?,?,?)",
                (orphan_token, "deleted-user-id", auth._now(), valid_until),
            )
            raw.commit()
        finally:
            raw.close()
        for token in (expired_token, orphan_token):
            with self.subTest(token=token):
                client = ASGITestClient()
                client.cookies["matchiq_session"] = token
                self.assertEqual(client.request("GET", "/api/auth/me")[0], 401)

    def test_bearer_is_supported_and_legacy_session_header_is_rejected(self):
        token = self.user_a.cookies["matchiq_session"]
        client = ASGITestClient()
        status, _, data = client.request(
            "GET", "/api/auth/me", headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["user"]["email"], "user-a@example.test")
        legacy = ASGITestClient()
        self.assertEqual(
            legacy.request("GET", "/api/auth/me", headers={"X-MatchIQ-Session": token})[0],
            401,
        )

    def test_both_users_can_access_authenticated_workflow_apis(self):
        self.assertEqual(self.user_a.request("GET", "/")[0], 200)
        for client, email in ((self.user_a, "user-a@example.test"), (self.user_b, "user-b@example.test")):
            for path in ("/api/projects", "/api/campaigns", "/api/media"):
                with self.subTest(email=email, path=path):
                    self.assertEqual(client.request("GET", path)[0], 200)
            self.assertEqual(client.request("POST", "/api/projects", json_body={"name": email})[0], 200)
            self.assertEqual(client.request("POST", "/api/campaigns", json_body={"name": email})[0], 200)
            status, _, storyboard = client.request("POST", "/api/reels/storyboard", json_body={})
            self.assertEqual(status, 200)
            self.assertTrue(storyboard["scenes"])
            boundary = "matchiq-test-boundary"
            multipart = (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"tiny.png\"\r\n"
                f"Content-Type: image/png\r\n\r\n"
            ).encode("ascii") + tiny_png() + f"\r\n--{boundary}--\r\n".encode("ascii")
            status, _, asset = client.request(
                "POST", "/api/media/upload", body=multipart,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )
            self.assertEqual(status, 200)
            self.assertEqual(asset["media_type"], "image")

    def test_render_endpoints_require_auth_and_authenticated_user_can_enqueue(self):
        payload = {"brand_name": "Test", "title": "Test", "topic": "Test"}
        anonymous = ASGITestClient()
        self.assertEqual(anonymous.request("POST", "/api/reels/create", json_body=payload)[0], 401)
        storyboard = {
            "brand_name": "Test", "topic": "Test", "hook": "Hook",
            "creative_direction": "", "music_mood": "", "rhythm": "", "scenes": [],
        }
        with patch.object(reels.executor, "submit") as submit:
            status, _, data = self.user_a.request("POST", "/api/reels/create", json_body=payload)
            render_status, _, render_data = self.user_a.request(
                "POST", "/api/reels/render-storyboard", json_body={"storyboard": storyboard},
            )
        self.assertEqual(status, 200)
        self.assertEqual(render_status, 200)
        self.assertTrue(data["job_id"])
        self.assertTrue(render_data["job_id"])
        self.assertEqual(submit.call_count, 2)
        status, _, job = self.user_a.request("GET", f"/api/reels/status/{data['job_id']}")
        self.assertEqual(status, 200)
        self.assertEqual(job["status"], "queued")
        reels.JOBS.pop(data["job_id"], None)
        reels.JOBS.pop(render_data["job_id"], None)

    def test_authenticated_storyboard_render_produces_mp4(self):
        storyboard = {
            "brand_name": "Test", "topic": "Test", "hook": "Test hook",
            "creative_direction": "", "music_mood": "cinematic", "rhythm": "balanced",
            "scenes": [{
                "index": 1, "title": "Hook", "visual": "Test", "camera": "Push-in",
                "motion": "Slow zoom", "lighting": "Clean", "voice_over": "", "subtitle": "Test",
                "duration_seconds": 1,
            }],
        }
        with tempfile.TemporaryDirectory(prefix="matchiq-render-test-") as render_dir:
            with patch.object(reel_renderer, "RENDERS_DIR", Path(render_dir)):
                with patch.object(reels.executor, "submit", side_effect=lambda fn, *args: fn(*args)):
                    status, _, data = self.user_a.request(
                        "POST", "/api/reels/render-storyboard",
                        json_body={"storyboard": storyboard, "music_enabled": False, "voice_enabled": False, "export_quality": "turbo"},
                    )
            self.assertEqual(status, 200)
            status, _, job = self.user_a.request("GET", f"/api/reels/status/{data['job_id']}")
            self.assertEqual(status, 200)
            self.assertEqual(job["status"], "done", job)
            output_path = Path(render_dir) / auth._get_user_by_email("user-a@example.test")["id"] / job["filename"]
            self.assertTrue(output_path.is_file())
            self.assertGreater(output_path.stat().st_size, 0)
            reels.JOBS.pop(data["job_id"], None)

    def test_public_endpoints_and_idempotent_logout(self):
        self.assertEqual(ASGITestClient().request("GET", "/api/health")[0], 200)
        self.assertEqual(ASGITestClient().request("GET", "/api/auth/health")[0], 200)
        anonymous = ASGITestClient()
        self.assertEqual(anonymous.request("POST", "/api/auth/logout")[0], 200)

        token = self.user_a.cookies["matchiq_session"]
        self.assertEqual(self.user_a.request("POST", "/api/auth/logout")[0], 200)
        self.assertNotIn("matchiq_session", self.user_a.cookies)
        bearer = ASGITestClient()
        self.assertEqual(bearer.request("GET", "/api/auth/me", headers={"Authorization": f"Bearer {token}"})[0], 401)


if __name__ == "__main__":
    unittest.main()
