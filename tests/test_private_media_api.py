import hashlib
from io import BytesIO
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from test_auth_api import ASGITestClient

from backend.app.render import reel_renderer
from backend.app.routers import auth, files, media, reels


def tiny_png():
    output = BytesIO()
    Image.new("RGBA", (1, 1), (20, 80, 120, 255)).save(output, format="PNG")
    return output.getvalue()


class PrivateMediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registrar = ASGITestClient()
        for name, email in (
            ("Private Media A", "private-media-a@example.test"),
            ("Private Media B", "private-media-b@example.test"),
        ):
            status, _, data = registrar.request(
                "POST", "/api/auth/register",
                json_body={"name": name, "email": email, "password": "strong-test-password"},
            )
            if status != 200 or not data.get("success"):
                raise AssertionError(f"Test account registration failed: {status} {data}")
        cls.user_a_id = auth._get_user_by_email("private-media-a@example.test")["id"]
        cls.user_b_id = auth._get_user_by_email("private-media-b@example.test")["id"]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="matchiq-private-media-")
        self.storage = Path(self.temp.name)
        self.uploads = self.storage / "uploads"
        self.renders = self.storage / "renders"
        self.uploads.mkdir()
        self.renders.mkdir()
        self.patches = [
            patch.object(media, "UPLOADS_DIR", self.uploads),
            patch.object(files, "UPLOADS_DIR", self.uploads),
            patch.object(files, "RENDERS_DIR", self.renders),
            patch.object(reel_renderer, "UPLOADS_DIR", self.uploads),
            patch.object(reel_renderer, "RENDERS_DIR", self.renders),
        ]
        for item in self.patches:
            item.start()
        self.user_a = self._login("private-media-a@example.test")
        self.user_b = self._login("private-media-b@example.test")

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def _login(self, email):
        client = ASGITestClient()
        status, _, data = client.request(
            "POST", "/api/auth/login",
            json_body={"email": email, "password": "strong-test-password"},
        )
        self.assertEqual(status, 200, data)
        self.assertIn("matchiq_session", client.cookies)
        return client

    def _upload(self, client, filename="tiny.png", data=None):
        data = tiny_png() if data is None else data
        boundary = "private-media-boundary"
        multipart = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
            "Content-Type: image/png\r\n\r\n"
        ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
        return client.request(
            "POST", "/api/media/upload", body=multipart,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )

    def _storyboard_payload(self, image_url=None):
        return {
            "storyboard": {
                "brand_name": "MatchIQ", "topic": "Private render", "hook": "Test hook",
                "creative_direction": "", "music_mood": "cinematic", "rhythm": "balanced",
                "scenes": [{
                    "index": 1, "title": "Hook", "visual": "Test", "camera": "Push-in",
                    "motion": "Slow zoom", "lighting": "Clean", "voice_over": "", "subtitle": "Private",
                    "image_url": image_url, "duration_seconds": 1,
                }],
            },
            "music_enabled": False, "voice_enabled": False, "export_quality": "turbo",
        }

    def test_media_list_private_serving_range_and_legacy_quarantine(self):
        legacy_name = "media_aaaaaaaaaaaa.png"
        legacy_path = self.uploads / legacy_name
        legacy_path.write_bytes(b"legacy upload bytes")
        legacy_hash = hashlib.sha256(legacy_path.read_bytes()).hexdigest()

        status_a, _, asset_a = self._upload(self.user_a)
        status_b, _, asset_b = self._upload(self.user_b)
        self.assertEqual(status_a, 200, asset_a)
        self.assertEqual(status_b, 200, asset_b)
        self.assertTrue((self.uploads / self.user_a_id / asset_a["filename"]).is_file())
        self.assertTrue((self.uploads / self.user_b_id / asset_b["filename"]).is_file())

        status, _, listed_a = self.user_a.request("GET", "/api/media")
        self.assertEqual(status, 200)
        self.assertEqual([item["filename"] for item in listed_a], [asset_a["filename"]])
        status, _, listed_b = self.user_b.request("GET", "/api/media")
        self.assertEqual(status, 200)
        self.assertEqual([item["filename"] for item in listed_b], [asset_b["filename"]])

        status, headers, body = self.user_a.request("GET", asset_a["url"])
        self.assertEqual(status, 200)
        self.assertEqual(body, tiny_png())
        self.assertIn(("cache-control", "private, no-store"), headers)
        self.assertIn(("x-content-type-options", "nosniff"), headers)
        self.assertEqual(self.user_b.request("GET", asset_a["url"])[0], 404)
        self.assertEqual(ASGITestClient().request("GET", asset_a["url"])[0], 401)
        self.assertEqual(self.user_a.request("GET", f"/uploads/{legacy_name}")[0], 404)
        self.assertEqual(self.user_b.request("GET", f"/uploads/{legacy_name}")[0], 404)

        range_status, range_headers, range_body = self.user_a.request(
            "GET", asset_a["url"], headers={"Range": "bytes=0-7"},
        )
        self.assertEqual(range_status, 206)
        self.assertEqual(range_body, tiny_png()[:8])
        self.assertIn(("accept-ranges", "bytes"), range_headers)
        self.assertEqual(self.user_a.request("GET", "/uploads/%2e%2e%5csecret.png")[0], 404)

        self.assertEqual(hashlib.sha256(legacy_path.read_bytes()).hexdigest(), legacy_hash)
        self.assertEqual(legacy_path.read_bytes(), b"legacy upload bytes")

    def test_chunked_upload_limit_removes_partial_file(self):
        with patch.object(media, "MAX_IMAGE_UPLOAD_BYTES", 4):
            status, _, _ = self._upload(self.user_a, data=b"12345")
        self.assertEqual(status, 413)
        user_dir = self.uploads / self.user_a_id
        self.assertEqual(list(user_dir.iterdir()), [])

        status, _, _ = self._upload(self.user_a, data=b"not an image")
        self.assertEqual(status, 400)
        self.assertEqual(list(user_dir.iterdir()), [])

    def test_job_status_and_render_files_are_owner_scoped(self):
        upload_status, _, asset = self._upload(self.user_a)
        self.assertEqual(upload_status, 200, asset)

        status, _, project_data = self.user_a.request("POST", "/api/projects", json_body={"name": "Private flow"})
        self.assertEqual(status, 200, project_data)
        status, _, campaign_data = self.user_a.request(
            "POST", "/api/campaigns", json_body={"name": "Private flow campaign", "project_id": project_data["project"]["id"]},
        )
        self.assertEqual(status, 200, campaign_data)
        status, _, storyboard = self.user_a.request(
            "POST", "/api/reels/storyboard", json_body={"brand_name": "MatchIQ", "topic": "Private flow"},
        )
        self.assertEqual(status, 200, storyboard)
        self.assertTrue(storyboard["scenes"])

        legacy_name = "matchiq_studio_reel_aaaaaaaaaa.mp4"
        legacy_path = self.renders / legacy_name
        legacy_path.write_bytes(b"legacy render bytes")
        legacy_hash = hashlib.sha256(legacy_path.read_bytes()).hexdigest()

        with patch.object(reels.executor, "submit", side_effect=lambda fn, *args: fn(*args)):
            status, _, job_data = self.user_a.request(
                "POST", "/api/reels/render-storyboard",
                json_body=self._storyboard_payload(asset["url"]),
            )
        self.assertEqual(status, 200, job_data)
        job_id = job_data["job_id"]
        status, _, job = self.user_a.request("GET", f"/api/reels/status/{job_id}")
        self.assertEqual(status, 200, job)
        self.assertEqual(job["status"], "done", job)
        self.assertEqual(self.user_b.request("GET", f"/api/reels/status/{job_id}")[0], 404)
        self.assertEqual(self.user_a.request("GET", "/api/reels/status/no-such-job")[0], 404)

        output = self.renders / self.user_a_id / job["filename"]
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 0)
        self.assertTrue((self.renders / ".work" / self.user_a_id).is_dir())
        self.assertEqual(job["render_url"], f"/renders/{job['filename']}")
        download_status, _, downloaded_mp4 = self.user_a.request("GET", job["render_url"])
        self.assertEqual(download_status, 200)
        self.assertEqual(downloaded_mp4, output.read_bytes())
        playback_status, playback_headers, mp4 = self.user_a.request(
            "GET", job["render_url"], headers={"Range": "bytes=0-31"},
        )
        self.assertEqual(playback_status, 206)
        self.assertEqual(len(mp4), 32)
        self.assertEqual(mp4[4:8], b"ftyp")
        self.assertIn(("cache-control", "private, no-store"), playback_headers)
        self.assertEqual(self.user_b.request("GET", job["render_url"])[0], 404)
        self.assertEqual(ASGITestClient().request("GET", job["render_url"])[0], 401)
        self.assertEqual(self.user_a.request("GET", f"/renders/{legacy_name}")[0], 404)
        self.assertEqual(self.user_a.request("GET", "/renders/scene_1.png")[0], 404)
        self.assertEqual(hashlib.sha256(legacy_path.read_bytes()).hexdigest(), legacy_hash)
        self.assertEqual(legacy_path.read_bytes(), b"legacy render bytes")
        reels.JOBS.pop(job_id, None)

    def test_renderer_rejects_other_user_and_traversal_inputs(self):
        status, _, asset_b = self._upload(self.user_b)
        self.assertEqual(status, 200, asset_b)
        for hostile_url in (
            asset_b["url"],
            "/uploads/../outside.png",
            "/uploads/%2e%2e%2foutside.png",
            "C:\\outside.png",
        ):
            with self.subTest(hostile_url=hostile_url):
                with patch.object(reels.executor, "submit", side_effect=lambda fn, *args: fn(*args)):
                    status, _, job_data = self.user_a.request(
                        "POST", "/api/reels/render-storyboard",
                        json_body=self._storyboard_payload(hostile_url),
                    )
                self.assertEqual(status, 200)
                status, _, job = self.user_a.request("GET", f"/api/reels/status/{job_data['job_id']}")
                self.assertEqual(status, 200)
                self.assertEqual(job["status"], "error")
                self.assertIsNone(job["render_url"])
                reels.JOBS.pop(job_data["job_id"], None)

        status, _, music_b = self._upload(self.user_b, filename="track.mp3", data=b"private audio bytes")
        self.assertEqual(status, 200, music_b)
        payload = self._storyboard_payload()
        payload["music_enabled"] = True
        payload["music_track_url"] = music_b["url"]
        with patch.object(reels.executor, "submit", side_effect=lambda fn, *args: fn(*args)):
            status, _, job_data = self.user_a.request(
                "POST", "/api/reels/render-storyboard", json_body=payload,
            )
        self.assertEqual(status, 200)
        status, _, job = self.user_a.request("GET", f"/api/reels/status/{job_data['job_id']}")
        self.assertEqual(status, 200)
        self.assertEqual(job["status"], "error")
        reels.JOBS.pop(job_data["job_id"], None)

    def test_file_and_owner_directory_symlinks_are_rejected(self):
        status, _, asset = self._upload(self.user_a)
        self.assertEqual(status, 200, asset)
        user_dir = self.uploads / self.user_a_id
        external_file = self.storage / "outside.png"
        external_file.write_bytes(tiny_png())
        file_link = user_dir / "media_bbbbbbbbbbbb.png"
        try:
            os.symlink(external_file, file_link)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation is unavailable in this environment.")
        self.assertEqual(self.user_a.request("GET", f"/uploads/{file_link.name}")[0], 404)
        self.assertNotIn(file_link.name, [item["filename"] for item in self.user_a.request("GET", "/api/media")[2]])

        owner_dir = self.uploads / self.user_b_id
        owner_dir.mkdir()
        moved_dir = self.uploads / f"{self.user_b_id}_real"
        owner_dir.rename(moved_dir)
        os.symlink(moved_dir, owner_dir, target_is_directory=True)
        self.assertEqual(self.user_b.request("GET", "/api/media")[0], 404)


if __name__ == "__main__":
    unittest.main()
