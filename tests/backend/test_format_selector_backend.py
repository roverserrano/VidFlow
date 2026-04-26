from backend.services.format_selector import build_quality_options, default_video_selector, progressive_video_selector


def test_facebook_quality_selector_prefers_progressive_mp4():
    raw = {
        "extractor_key": "Facebook",
        "formats": [
            {
                "format_id": "dash1",
                "ext": "mp4",
                "height": 720,
                "vcodec": "avc1.64001F",
                "acodec": "none",
                "tbr": 2000,
            },
            {
                "format_id": "prog1",
                "ext": "mp4",
                "height": 720,
                "vcodec": "avc1.64001F",
                "acodec": "mp4a.40.2",
                "tbr": 1800,
            },
        ],
    }

    options = build_quality_options(raw)

    assert options
    assert "+bestaudio" not in options[0].selector
    assert options[0].selector.startswith("best[height<=")


def test_facebook_default_selector_avoids_dash_merge():
    selector = default_video_selector(facebook_mode=True)
    assert "+bestaudio" not in selector
    assert selector.startswith("best[ext=mp4]")


def test_default_selector_avoids_hevc_when_possible():
    selector = default_video_selector(facebook_mode=False)
    assert "vcodec!*=hevc" in selector
    assert "vcodec!*=hvc1" in selector
    assert "vcodec!*=h265" in selector
    assert "vcodec!*=dvh1" in selector


def test_progressive_selector_uses_mp4_compat_codecs():
    selector = progressive_video_selector(1080)
    assert selector.startswith("best[height<=1080]")
    assert "[acodec^=mp4a]" in selector
    assert "vcodec!*=h265" in selector
