import json
from io import BytesIO
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from test_auth_api import ASGITestClient

from backend.app.project import project_store
from backend.app.campaigns import campaign_store
from backend.app.render import reel_renderer
from backend.app.routers import auth, media, reels


def tiny_png():
    output = BytesIO()
    Image.new("RGBA", (1, 1), (20, 80, 120, 255)).save(output, format="PNG")
    return output.getvalue()


class OwnershipIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registrar = ASGITestClient()
        for name, email in (
            ("Ownership A", "ownership-a@example.test"),
            ("Ownership B", "ownership-b@example.test"),
        ):
            status, _, data = cls.registrar.request(
                "POST", "/api/auth/register",
                json_body={"name": name, "email": email, "password": "strong-test-password"},
            )
            if status != 200 or not data.get("success"):
                raise AssertionError(f"Test account registration failed: {status} {data}")
        cls.user_a_id = auth._get_user_by_email("ownership-a@example.test")["id"]
        cls.user_b_id = auth._get_user_by_email("ownership-b@example.test")["id"]

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="matchiq-ownership-tests-")
        self.storage = Path(self.temp_dir.name)
        self.project_file_patch = patch.object(project_store, "PROJECTS_FILE", self.storage / "projects.json")
        self.campaign_file_patch = patch.object(campaign_store, "CAMPAIGNS_FILE", self.storage / "campaigns.json")
        self.upload_dir_patch = patch.object(media, "UPLOADS_DIR", self.storage / "uploads")
        self.project_file_patch.start()
        self.campaign_file_patch.start()
        self.upload_dir_patch.start()
        media.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        self.user_a = self._login("ownership-a@example.test")
        self.user_b = self._login("ownership-b@example.test")

    def tearDown(self):
        self.upload_dir_patch.stop()
        self.campaign_file_patch.stop()
        self.project_file_patch.stop()
        self.temp_dir.cleanup()

    def _login(self, email):
        client = ASGITestClient()
        status, _, data = client.request(
            "POST", "/api/auth/login",
            json_body={"email": email, "password": "strong-test-password"},
        )
        self.assertEqual(status, 200, data)
        self.assertIn("matchiq_session", client.cookies)
        return client

    def _create_project(self, client, name, **extra):
        status, _, data = client.request(
            "POST", "/api/projects", json_body={"name": name, **extra},
        )
        self.assertEqual(status, 200, data)
        return data["project"]

    def _create_campaign(self, client, name, project_id=None, **extra):
        status, _, data = client.request(
            "POST", "/api/campaigns",
            json_body={"name": name, "project_id": project_id, **extra},
        )
        self.assertEqual(status, 200, data)
        return data["campaign"]

    def test_projects_are_scoped_and_updates_never_upsert(self):
        project_a = self._create_project(
            self.user_a, "Project A", owner_user_id=self.user_b_id, user_id=self.user_b_id,
        )
        project_b = self._create_project(self.user_b, "Project B")
        self.assertNotIn("owner_user_id", project_a)

        raw = json.loads(project_store.PROJECTS_FILE.read_text(encoding="utf-8"))
        owners = {item["id"]: item["owner_user_id"] for item in raw}
        self.assertEqual(owners[project_a["id"]], self.user_a_id)
        self.assertEqual(owners[project_b["id"]], self.user_b_id)

        status, _, data = self.user_a.request("GET", "/api/projects")
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in data["projects"]], [project_a["id"]])
        status, _, data = self.user_b.request("GET", "/api/projects")
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in data["projects"]], [project_b["id"]])

        self.assertEqual(self.user_a.request("GET", f"/api/projects/{project_a['id']}")[0], 200)
        self.assertEqual(self.user_b.request("GET", f"/api/projects/{project_b['id']}")[0], 200)
        self.assertEqual(self.user_a.request("GET", f"/api/projects/{project_b['id']}")[0], 404)
        self.assertEqual(self.user_b.request("GET", f"/api/projects/{project_a['id']}")[0], 404)
        status, _, updated = self.user_a.request(
            "PUT", f"/api/projects/{project_a['id']}", json_body={"name": "Project A updated"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["project"]["name"], "Project A updated")

        before = project_store.PROJECTS_FILE.read_text(encoding="utf-8")
        self.assertEqual(
            self.user_a.request("PUT", f"/api/projects/{project_b['id']}", json_body={"name": "stolen"})[0],
            404,
        )
        self.assertEqual(
            self.user_a.request("PUT", "/api/projects/missing-project", json_body={"name": "implicit"})[0],
            404,
        )
        self.assertEqual(project_store.PROJECTS_FILE.read_text(encoding="utf-8"), before)
        self.assertEqual(len(json.loads(before)), 2)

    def test_campaigns_are_scoped_and_campaign_ids_cannot_cross_users(self):
        project_a = self._create_project(self.user_a, "Project A")
        project_b = self._create_project(self.user_b, "Project B")
        campaign_a = self._create_campaign(
            self.user_a, "Campaign A", project_a["id"],
            owner_user_id=self.user_b_id, user_id=self.user_b_id,
        )
        campaign_b = self._create_campaign(self.user_b, "Campaign B", project_b["id"])
        self.assertNotIn("owner_user_id", campaign_a)

        raw = json.loads(campaign_store.CAMPAIGNS_FILE.read_text(encoding="utf-8"))
        owners = {item["id"]: item["owner_user_id"] for item in raw}
        self.assertEqual(owners[campaign_a["id"]], self.user_a_id)
        self.assertEqual(owners[campaign_b["id"]], self.user_b_id)

        status, _, data = self.user_a.request("GET", "/api/campaigns")
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in data["campaigns"]], [campaign_a["id"]])
        status, _, data = self.user_b.request("GET", "/api/campaigns")
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in data["campaigns"]], [campaign_b["id"]])

        self.assertEqual(self.user_a.request("GET", f"/api/campaigns/{campaign_b['id']}")[0], 404)
        self.assertEqual(self.user_b.request("GET", f"/api/campaigns/{campaign_a['id']}")[0], 404)
        status, _, updated = self.user_a.request(
            "PUT", f"/api/campaigns/{campaign_a['id']}",
            json_body={"name": "Campaign A updated", "project_id": project_a["id"]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["campaign"]["name"], "Campaign A updated")
        before = campaign_store.CAMPAIGNS_FILE.read_text(encoding="utf-8")
        self.assertEqual(
            self.user_a.request(
                "PUT", f"/api/campaigns/{campaign_b['id']}",
                json_body={"name": "stolen", "project_id": project_a["id"]},
            )[0],
            404,
        )
        self.assertEqual(
            self.user_a.request("PUT", "/api/campaigns/missing-campaign", json_body={"name": "implicit"})[0],
            404,
        )
        self.assertEqual(campaign_store.CAMPAIGNS_FILE.read_text(encoding="utf-8"), before)
        self.assertEqual(len(json.loads(before)), 2)

    def test_campaign_parent_project_must_belong_to_current_user(self):
        project_a = self._create_project(self.user_a, "Project A")
        project_b = self._create_project(self.user_b, "Project B")

        for client, foreign_project in ((self.user_a, project_b), (self.user_b, project_a)):
            with self.subTest(foreign_project=foreign_project["id"]):
                status, _, _ = client.request(
                    "POST", "/api/campaigns",
                    json_body={"name": "must not link", "project_id": foreign_project["id"]},
                )
                self.assertEqual(status, 404)
        self.assertEqual(campaign_store.CAMPAIGNS_FILE.exists(), False)

        campaign_a = self._create_campaign(self.user_a, "Owned campaign", project_a["id"])
        status, _, _ = self.user_a.request(
            "PUT", f"/api/campaigns/{campaign_a['id']}",
            json_body={"name": "cross-link", "project_id": project_b["id"]},
        )
        self.assertEqual(status, 404)
        self.assertEqual(campaign_store.get_campaign(campaign_a["id"], self.user_a_id).project_id, project_a["id"])

    def test_standalone_campaign_is_owned_and_private(self):
        campaign = self._create_campaign(self.user_a, "Standalone campaign")
        stored = json.loads(campaign_store.CAMPAIGNS_FILE.read_text(encoding="utf-8"))
        record = next(item for item in stored if item["id"] == campaign["id"])
        self.assertIsNone(record["project_id"])
        self.assertEqual(record["owner_user_id"], self.user_a_id)
        self.assertEqual(self.user_a.request("GET", f"/api/campaigns/{campaign['id']}")[0], 200)
        self.assertEqual(self.user_b.request("GET", f"/api/campaigns/{campaign['id']}")[0], 404)
        self.assertEqual(
            self.user_b.request("PUT", f"/api/campaigns/{campaign['id']}", json_body={"name": "stolen"})[0],
            404,
        )

    def test_update_payload_cannot_transfer_project_or_campaign_ownership(self):
        project = self._create_project(self.user_a, "Owned project")
        status, _, data = self.user_a.request(
            "PUT", f"/api/projects/{project['id']}",
            json_body={"name": "Still owned", "owner_user_id": self.user_b_id},
        )
        self.assertEqual(status, 200, data)
        project_items = json.loads(project_store.PROJECTS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(next(item for item in project_items if item["id"] == project["id"])["owner_user_id"], self.user_a_id)
        self.assertEqual(self.user_b.request("GET", f"/api/projects/{project['id']}")[0], 404)

        campaign = self._create_campaign(self.user_a, "Owned standalone campaign")
        status, _, data = self.user_a.request(
            "PUT", f"/api/campaigns/{campaign['id']}",
            json_body={"name": "Still owned", "owner_user_id": self.user_b_id},
        )
        self.assertEqual(status, 200, data)
        campaign_items = json.loads(campaign_store.CAMPAIGNS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(next(item for item in campaign_items if item["id"] == campaign["id"])["owner_user_id"], self.user_a_id)
        self.assertEqual(self.user_b.request("GET", f"/api/campaigns/{campaign['id']}")[0], 404)

    def test_missing_and_valid_empty_json_stores_allow_creation(self):
        self.assertFalse(project_store.PROJECTS_FILE.exists())
        self.assertFalse(campaign_store.CAMPAIGNS_FILE.exists())
        self._create_project(self.user_a, "Created with absent project store")
        self._create_campaign(self.user_a, "Created with absent campaign store")

        project_store.PROJECTS_FILE.write_text("[]", encoding="utf-8")
        campaign_store.CAMPAIGNS_FILE.write_text("[]", encoding="utf-8")
        self._create_project(self.user_a, "Created with empty project store")
        self._create_campaign(self.user_a, "Created with empty campaign store")

    def test_malformed_json_fails_without_overwriting_existing_storage(self):
        invalid_projects = b'{"records":['
        invalid_campaigns = b'{"records":['
        project_store.PROJECTS_FILE.write_bytes(invalid_projects)
        campaign_store.CAMPAIGNS_FILE.write_bytes(invalid_campaigns)

        with self.assertRaises(json.JSONDecodeError):
            self.user_a.request("POST", "/api/projects", json_body={"name": "must not be written"})
        with self.assertRaises(json.JSONDecodeError):
            self.user_a.request("POST", "/api/campaigns", json_body={"name": "must not be written"})

        self.assertEqual(project_store.PROJECTS_FILE.read_bytes(), invalid_projects)
        self.assertEqual(campaign_store.CAMPAIGNS_FILE.read_bytes(), invalid_campaigns)

    def test_legacy_records_are_quarantined_and_preserved(self):
        legacy_project = {
            "id": "legacy-project-id", "name": "Legacy project",
            "created_at": "2025-01-01T00:00:00+00:00", "updated_at": "2025-01-01T00:00:00+00:00",
        }
        legacy_campaign = {
            "id": "legacy-campaign-id", "name": "Legacy campaign", "project_id": legacy_project["id"],
            "created_at": "2025-01-01T00:00:00+00:00", "updated_at": "2025-01-01T00:00:00+00:00",
        }
        project_store.PROJECTS_FILE.write_text(json.dumps([legacy_project]), encoding="utf-8")
        campaign_store.CAMPAIGNS_FILE.write_text(json.dumps([legacy_campaign]), encoding="utf-8")
        projects_before = project_store.PROJECTS_FILE.read_text(encoding="utf-8")
        campaigns_before = campaign_store.CAMPAIGNS_FILE.read_text(encoding="utf-8")

        for client in (self.user_a, self.user_b):
            self.assertEqual(client.request("GET", "/api/projects")[2]["projects"], [])
            self.assertEqual(client.request("GET", "/api/campaigns")[2]["campaigns"], [])
            self.assertEqual(client.request("GET", f"/api/projects/{legacy_project['id']}")[0], 404)
            self.assertEqual(client.request("GET", f"/api/campaigns/{legacy_campaign['id']}")[0], 404)
            self.assertEqual(client.request("PUT", f"/api/projects/{legacy_project['id']}", json_body={"name": "claim"})[0], 404)
            self.assertEqual(client.request("PUT", f"/api/campaigns/{legacy_campaign['id']}", json_body={"name": "claim"})[0], 404)

        self.assertEqual(project_store.PROJECTS_FILE.read_text(encoding="utf-8"), projects_before)
        self.assertEqual(campaign_store.CAMPAIGNS_FILE.read_text(encoding="utf-8"), campaigns_before)
        self._create_project(self.user_a, "New owned project")
        self._create_campaign(self.user_a, "New owned campaign")
        self.assertEqual(json.loads(project_store.PROJECTS_FILE.read_text(encoding="utf-8"))[0], legacy_project)
        self.assertEqual(json.loads(campaign_store.CAMPAIGNS_FILE.read_text(encoding="utf-8"))[0], legacy_campaign)

    def test_owned_project_campaign_storyboard_media_render_workflow(self):
        project = self._create_project(self.user_a, "Workflow project")
        campaign = self._create_campaign(self.user_a, "Workflow campaign", project["id"])
        self.assertEqual(campaign["project_id"], project["id"])

        status, _, storyboard = self.user_a.request(
            "POST", "/api/reels/storyboard",
            json_body={"brand_name": "Test", "title": "Owned", "topic": "Workflow"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(storyboard["scenes"])

        boundary = "ownership-media-boundary"
        multipart = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"tiny.png\"\r\n"
            "Content-Type: image/png\r\n\r\n"
        ).encode("ascii") + tiny_png() + f"\r\n--{boundary}--\r\n".encode("ascii")
        status, _, asset = self.user_a.request(
            "POST", "/api/media/upload", body=multipart,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(asset["media_type"], "image")

        test_storyboard = {
            "brand_name": "Test", "topic": "Workflow", "hook": "Owned hook",
            "creative_direction": "", "music_mood": "cinematic", "rhythm": "balanced",
            "scenes": [{
                "index": 1, "title": "Hook", "visual": "Test", "camera": "Push-in",
                "motion": "Slow zoom", "lighting": "Clean", "voice_over": "", "subtitle": "Owned",
                "duration_seconds": 1,
            }],
        }
        with tempfile.TemporaryDirectory(prefix="matchiq-ownership-render-") as render_dir:
            with patch.object(reel_renderer, "RENDERS_DIR", Path(render_dir)):
                with patch.object(reels.executor, "submit", side_effect=lambda fn, *args: fn(*args)):
                    status, _, job_data = self.user_a.request(
                        "POST", "/api/reels/render-storyboard",
                        json_body={
                            "storyboard": test_storyboard, "music_enabled": False,
                            "voice_enabled": False, "export_quality": "turbo",
                        },
                    )
            self.assertEqual(status, 200)
            status, _, job = self.user_a.request("GET", f"/api/reels/status/{job_data['job_id']}")
            self.assertEqual(status, 200)
            self.assertEqual(job["status"], "done", job)
            self.assertTrue((Path(render_dir) / self.user_a_id / job["filename"]).is_file())
            reels.JOBS.pop(job_data["job_id"], None)

        self.assertEqual(self.user_b.request("GET", f"/api/projects/{project['id']}")[0], 404)
        self.assertEqual(self.user_b.request("GET", f"/api/campaigns/{campaign['id']}")[0], 404)


if __name__ == "__main__":
    unittest.main()
