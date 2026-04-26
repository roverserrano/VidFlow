from backend.models import DownloadRequest, DownloadType, Platform
from backend.services.ytdlp_service import YtDlpService


class FakeYoutubeDL:
    def __init__(self, options):
        self.options = options

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def extract_info(self, url, download=False):
        return {
            "title": "Demo",
            "webpage_url": url,
            "duration": 90,
            "thumbnail": "https://example.test/thumb.jpg",
            "formats": [
                {
                    "format_id": "137",
                    "ext": "mp4",
                    "height": 1080,
                    "fps": 30,
                    "vcodec": "avc1.640028",
                    "acodec": "none",
                    "filesize": 1024,
                }
            ],
        }


def test_analyze_uses_ytdlp_and_returns_metadata(monkeypatch):
    service = YtDlpService()
    monkeypatch.setattr(service, "_ydl_class", lambda: FakeYoutubeDL)

    metadata = service.analyze("https://youtu.be/demo", Platform.YOUTUBE)

    assert metadata.title == "Demo"
    assert metadata.platform == Platform.YOUTUBE
    assert metadata.formats[0].resolution == "1080p"


def test_analyze_normalizes_float_duration(monkeypatch):
    class FakeDurationYoutubeDL(FakeYoutubeDL):
        def extract_info(self, url, download=False):
            data = super().extract_info(url, download)
            data["duration"] = 6.57
            return data

    service = YtDlpService()
    monkeypatch.setattr(service, "_ydl_class", lambda: FakeDurationYoutubeDL)

    metadata = service.analyze("https://www.facebook.com/share/r/1Puiv3ZQJn/", Platform.FACEBOOK)

    assert metadata.duration == 7
    assert metadata.duration_text == "0:07"


def test_audio_download_options_extract_mp3():
    service = YtDlpService()
    request = DownloadRequest(
        url="https://youtu.be/demo",
        title="Demo",
        download_type=DownloadType.AUDIO,
        audio_format="mp3",
        output_dir="/tmp",
    )

    options = service._download_options(
        request=request,
        platform=Platform.YOUTUBE,
        output_template="/tmp/demo.%(ext)s",
        ffmpeg=None,
        progress_hook=lambda data: None,
    )

    assert options["format"] == "bestaudio/best"
    assert options["postprocessors"][0]["preferredcodec"] == "mp3"
    assert options["postprocessors"][0]["preferredquality"] == "192"


def test_video_download_options_without_ffmpeg_use_progressive_selector():
    service = YtDlpService()
    request = DownloadRequest(
        url="https://youtu.be/demo",
        title="Demo",
        download_type=DownloadType.VIDEO,
        resolution="1080p",
        output_dir="/tmp",
    )

    options = service._download_options(
        request=request,
        platform=Platform.YOUTUBE,
        output_template="/tmp/demo.%(ext)s",
        ffmpeg=None,
        progress_hook=lambda data: None,
    )

    assert options["format"].startswith("best[height<=1080]")
    assert "acodec^=mp4a" in options["format"]
    assert "merge_output_format" not in options


def test_tiktok_download_options_force_h264_selector():
    service = YtDlpService()
    request = DownloadRequest(
        url="https://www.tiktok.com/@demo/video/123",
        title="Demo",
        download_type=DownloadType.VIDEO,
        resolution="720p",
        output_dir="/tmp",
    )

    options = service._download_options(
        request=request,
        platform=Platform.TIKTOK,
        output_template="/tmp/demo.%(ext)s",
        ffmpeg=None,
        progress_hook=lambda data: None,
    )

    assert "format_id*=h264" in options["format"]
    assert options["format"].startswith("best[height<=720]")
    assert not options["format"].endswith("/best")
    assert "/best[ext=mp4]/best" not in options["format"]
