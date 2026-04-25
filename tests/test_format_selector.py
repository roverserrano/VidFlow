from __future__ import annotations

import unittest

from vidflow.services.format_selector import build_quality_options, decode_plan


class FormatSelectorTests(unittest.TestCase):
    def test_groups_formats_by_height_and_builds_compatible_plan(self):
        raw = {
            "extractor_key": "Youtube",
            "formats": [
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "height": 1080,
                    "fps": 30,
                    "vcodec": "avc1.640028",
                    "acodec": "none",
                    "tbr": 4200,
                },
                {
                    "format_id": "140",
                    "ext": "m4a",
                    "vcodec": "none",
                    "acodec": "mp4a.40.2",
                },
                {
                    "format_id": "22",
                    "ext": "mp4",
                    "height": 720,
                    "fps": 30,
                    "vcodec": "avc1.64001F",
                    "acodec": "mp4a.40.2",
                    "tbr": 1900,
                },
            ],
        }

        options = build_quality_options(raw)

        self.assertEqual([item.resolution for item in options], ["1080p", "720p"])
        plan = decode_plan(options[0].plan)
        self.assertEqual(plan["compatible"]["container"], "mp4")
        self.assertIn("137", plan["compatible"]["selector"])

    def test_facebook_prefers_non_av1_mp4_for_compatibility(self):
        raw = {
            "extractor_key": "Facebook",
            "formats": [
                {
                    "format_id": "av1",
                    "ext": "mp4",
                    "height": 720,
                    "fps": 30,
                    "vcodec": "av01.0.05M.08",
                    "acodec": "none",
                    "tbr": 2600,
                },
                {
                    "format_id": "h264",
                    "ext": "mp4",
                    "height": 720,
                    "fps": 30,
                    "vcodec": "avc1.64001F",
                    "acodec": "mp4a.40.2",
                    "tbr": 2100,
                },
            ],
        }

        options = build_quality_options(raw)

        self.assertEqual(len(options), 1)
        self.assertIn("H.264", options[0].label)
        plan = decode_plan(options[0].plan)
        self.assertEqual(plan["source_format_id"], "h264")


if __name__ == "__main__":
    unittest.main()
