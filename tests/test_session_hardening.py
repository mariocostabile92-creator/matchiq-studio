import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_auth_api import ASGITestClient

from backend.app.core import config
from backend.app.routers import auth


class SessionHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registrar = ASGITestClient()
        for name, email in (("Session A", "session-a@example.test"), ("Session B", "session-b@example.test")):
            status, _, data = cls.registrar.request(
                "POST", "/api/auth/register",
                json_body={"name": name, "email": email, "password": "strong-test-password"},
            )
            if status != 200 or not data.get("success"):
                raise AssertionError(f"Test account registration failed: {status} {data}")

    def _login(self, email="session-a@example.test"):
        client = ASGITestClient()
        status, headers, data = client.request(
            "POST", "/api/auth/login",
            json_body={"email": email, "password": "strong-test-password"},
        )
        self.assertEqual(status, 200, data)
        self.assertNotIn("session_token", data)
        self.assertIn("matchiq_session", client.cookies)
        set_cookie = next(value for key, value in headers if key == "set-cookie")
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("SameSite=lax", set_cookie)
        return client, set_cookie

    def test_login_and_registration_are_cookie_only_and_dev_cookie_is_explicitly_insecure(self):
        client, cookie = self._login()
        self.assertNotIn("Secure", cookie)
        self.assertEqual(client.request("GET", "/api/auth/me")[0], 200)

        fresh = ASGITestClient()
        status, headers, data = fresh.request(
            "POST", "/api/auth/register",
            json_body={"name": "Cookie Only", "email": "cookie-only@example.test", "password": "strong-test-password"},
        )
        self.assertEqual(status, 200, data)
        self.assertNotIn("session_token", data)
        self.assertTrue(any(key == "set-cookie" and "HttpOnly" in value for key, value in headers))

    def test_production_secure_cookie_setting_is_respected(self):
        with patch.object(auth, "SESSION_COOKIE_SECURE", True):
            _, cookie = self._login()
        self.assertIn("Secure", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=lax", cookie)

    def test_cookie_and_bearer_credentials_are_never_combined_or_fallback(self):
        user_a, _ = self._login("session-a@example.test")
        user_b, _ = self._login("session-b@example.test")
        token_a = user_a.cookies["matchiq_session"]
        token_b = user_b.cookies["matchiq_session"]
        cases = (
            ("valid cookie + valid bearer", token_a, token_a),
            ("valid cookie + invalid bearer", token_a, "not-a-session"),
            ("invalid cookie + valid bearer", "not-a-session", token_a),
            ("user A cookie + user B bearer", token_a, token_b),
        )
        for label, cookie_token, bearer_token in cases:
            with self.subTest(label=label):
                client = ASGITestClient()
                client.cookies["matchiq_session"] = cookie_token
                status, _, _ = client.request(
                    "GET", "/api/auth/me", headers={"Authorization": f"Bearer {bearer_token}"},
                )
                self.assertEqual(status, 401)

        bearer_client = ASGITestClient()
        status, _, data = bearer_client.request(
            "GET", "/api/auth/me", headers={"Authorization": f"Bearer {token_a}"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["user"]["email"], "session-a@example.test")

    def test_cookie_logout_revokes_session_and_uses_matching_cookie_attributes(self):
        client, _ = self._login()
        token = client.cookies["matchiq_session"]
        status, headers, data = client.request("POST", "/api/auth/logout")
        self.assertEqual(status, 200, data)
        self.assertNotIn("matchiq_session", client.cookies)
        clear_cookie = next(value for key, value in headers if key == "set-cookie")
        self.assertIn("HttpOnly", clear_cookie)
        self.assertIn("SameSite=lax", clear_cookie)
        self.assertNotIn("Secure", clear_cookie)
        self.assertEqual(
            ASGITestClient().request("GET", "/api/auth/me", headers={"Authorization": f"Bearer {token}"})[0],
            401,
        )

    def test_bearer_logout_revokes_session_and_mixed_logout_revokes_neither(self):
        client_a, _ = self._login("session-a@example.test")
        client_b, _ = self._login("session-b@example.test")
        token_a = client_a.cookies["matchiq_session"]
        token_b = client_b.cookies["matchiq_session"]

        mixed = ASGITestClient()
        mixed.cookies["matchiq_session"] = token_a
        status, _, _ = mixed.request(
            "POST", "/api/auth/logout", headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(client_a.request("GET", "/api/auth/me")[0], 200)
        self.assertEqual(
            ASGITestClient().request("GET", "/api/auth/me", headers={"Authorization": f"Bearer {token_b}"})[0],
            200,
        )

        bearer_only = ASGITestClient()
        status, _, _ = bearer_only.request(
            "POST", "/api/auth/logout", headers={"Authorization": f"Bearer {token_b}"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            ASGITestClient().request("GET", "/api/auth/me", headers={"Authorization": f"Bearer {token_b}"})[0],
            401,
        )

    def test_revoked_legacy_json_session_does_not_resurrect_after_reinitialization(self):
        client, _ = self._login()
        token = client.cookies["matchiq_session"]
        user_id = auth._get_user_by_email("session-a@example.test")["id"]
        with tempfile.TemporaryDirectory(prefix="matchiq-legacy-session-") as folder:
            legacy_path = Path(folder) / "sessions.json"
            with patch.object(auth, "SESSIONS_PATH", legacy_path):
                legacy_path.write_text(json.dumps({token: {"user_id": user_id}}), encoding="utf-8")
                self.assertEqual(
                    ASGITestClient().request("GET", "/api/auth/me", headers={"Authorization": f"Bearer {token}"})[0],
                    200,
                )
                auth._init_db()
                self.assertEqual(
                    ASGITestClient().request("GET", "/api/auth/me", headers={"Authorization": f"Bearer {token}"})[0],
                    200,
                )
                self.assertEqual(client.request("POST", "/api/auth/logout")[0], 200)
                auth._init_db()
                auth._init_db()
                self.assertTrue(legacy_path.exists())
                self.assertIn(token, legacy_path.read_text(encoding="utf-8"))
                self.assertEqual(
                    ASGITestClient().request("GET", "/api/auth/me", headers={"Authorization": f"Bearer {token}"})[0],
                    401,
                )

    def test_cookie_mutations_require_an_exact_allowed_origin(self):
        client, _ = self._login()
        allowed_status, _, created = client.request(
            "POST", "/api/projects", json_body={"name": "Origin allowed"},
            headers={"Origin": "https://studio.matchiq.it.com"},
        )
        self.assertEqual(allowed_status, 200, created)
        before = client.request("GET", "/api/projects")[2]["projects"]

        for origin in ("https://attacker.example", "null"):
            with self.subTest(origin=origin):
                status, _, _ = client.request(
                    "POST", "/api/projects", json_body={"name": "Must not persist"},
                    headers={"Origin": origin},
                )
                self.assertEqual(status, 403)

        status, _, _ = client.request(
            "POST", "/api/projects", json_body={"name": "Missing origin"}, omit_origin=True,
        )
        self.assertEqual(status, 403)
        after = client.request("GET", "/api/projects")[2]["projects"]
        self.assertEqual(after, before)

    def test_bearer_only_mutation_does_not_require_browser_origin(self):
        browser, _ = self._login()
        token = browser.cookies["matchiq_session"]
        api_client = ASGITestClient()
        status, _, data = api_client.request(
            "POST", "/api/projects", json_body={"name": "Bearer API"},
            headers={"Authorization": f"Bearer {token}"}, omit_origin=True,
        )
        self.assertEqual(status, 200, data)

    def test_cors_preflight_allows_only_configured_origins_and_methods(self):
        allowed, allowed_headers, _ = ASGITestClient().request(
            "OPTIONS", "/api/projects",
            headers={
                "Origin": "https://studio.matchiq.it.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )
        self.assertEqual(allowed, 200)
        self.assertIn(("access-control-allow-origin", "https://studio.matchiq.it.com"), allowed_headers)
        self.assertIn(("access-control-allow-credentials", "true"), allowed_headers)

        for origin in ("https://attacker.example", "null", "https://sub.studio.matchiq.it.com"):
            with self.subTest(origin=origin):
                status, headers, _ = ASGITestClient().request(
                    "OPTIONS", "/api/projects",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "content-type",
                    },
                )
                self.assertEqual(status, 400)
                self.assertNotIn("access-control-allow-origin", dict(headers))

    def test_trusted_hosts_accept_configured_production_and_dev_hosts_only(self):
        for host in ("studio.matchiq.it.com", "127.0.0.1", "localhost", "test-server"):
            with self.subTest(host=host):
                status, _, _ = ASGITestClient().request(
                    "GET", "/api/auth/health", headers={"Host": host},
                )
                self.assertEqual(status, 200)
        status, _, _ = ASGITestClient().request(
            "GET", "/api/auth/health", headers={"Host": "attacker.example"},
        )
        self.assertEqual(status, 400)
        status, _, health = ASGITestClient().request("GET", "/api/auth/health")
        self.assertEqual(status, 200)
        self.assertEqual(health, {"success": True})

    def test_pwa_auth_uses_cookie_and_never_persists_or_sends_tokens(self):
        api_source = (config.FRONTEND_DIR / "js" / "api.js").read_text(encoding="utf-8")
        app_source = (config.FRONTEND_DIR / "js" / "app.js").read_text(encoding="utf-8")
        sw_source = (config.FRONTEND_DIR / "sw.js").read_text(encoding="utf-8")
        index_source = (config.FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn('credentials: "same-origin"', api_source)
        self.assertIn('"matchiq_session_token"', api_source)
        self.assertNotIn("Authorization", api_source)
        self.assertNotIn("data?.session_token", api_source)
        self.assertNotIn("getStoredUser", app_source)
        self.assertNotIn("hasRememberedWorkspace", app_source)
        self.assertIn("const data = await getCurrentUser()", app_source)
        self.assertIn("showAuth(\"Accedi oppure registrati", app_source)
        self.assertIn("matchiq-studio-shell-v68", sw_source)
        self.assertIn("/js/api.js?v=68", index_source)


if __name__ == "__main__":
    unittest.main()
