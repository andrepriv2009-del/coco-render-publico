"""Guardrails for the current Coco renderer contract (no render required)."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RENDERER = (ROOT / "video/render_coco.py").read_text(encoding="utf-8")
PIPELINE = (ROOT / "scripts/generate_daily_coco.py").read_text(encoding="utf-8")
WORKFLOW = (ROOT / ".github/workflows/coco-daily-production.yml").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


class ProductionContractTests(unittest.TestCase):
    def test_blender_base_resolution_and_fps_match_pipeline(self):
        self.assertRegex(RENDERER, r"resolution_x\s*=\s*720")
        self.assertRegex(RENDERER, r"resolution_y\s*=\s*1280")
        self.assertRegex(RENDERER, r"render\.fps\s*=\s*30")
        self.assertIn("abs(base_fps - 30) <= 0.01", PIPELINE)

    def test_pipeline_final_master_is_1080_portrait_30fps(self):
        self.assertIn("WIDTH, HEIGHT, FPS, DURATION = 1080, 1920, 30, 60", PIPELINE)
        self.assertIn("video_stream.get(\"width\") != WIDTH", PIPELINE)
        self.assertIn("abs(fps - FPS) > 0.01", PIPELINE)

    def test_current_master_is_not_misrepresented_as_native_4k(self):
        self.assertIn("not native 4K", PIPELINE)
        self.assertIn("no es 4K nativo", README)

    def test_daily_workflow_keeps_youtube_publishing_disabled(self):
        self.assertIn("workflow_dispatch", WORKFLOW)
        self.assertIn("Publicación desactivada", WORKFLOW)
        self.assertNotRegex(WORKFLOW, r"youtube\.upload|upload_video|videos\?part=snippet")

    def test_single_scheduled_production_job_and_artifact_gate(self):
        self.assertEqual(len(re.findall(r"^\s+- cron:", WORKFLOW, re.MULTILINE)), 1)
        self.assertIn("actions/upload-artifact@v4", WORKFLOW)
        self.assertIn("if-no-files-found: error", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
