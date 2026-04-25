import pytest

from backend.models import Platform
from backend.models.errors import VidFlowError
from backend.utils.platform_detect import detect_platform


@pytest.mark.parametrize(
    ("url", "platform"),
    [
        ("https://www.youtube.com/watch?v=abc", Platform.YOUTUBE),
        ("https://youtu.be/abc", Platform.YOUTUBE),
        ("https://www.tiktok.com/@user/video/123", Platform.TIKTOK),
        ("https://www.facebook.com/watch/?v=123", Platform.FACEBOOK),
        ("https://fb.watch/abc", Platform.FACEBOOK),
    ],
)
def test_detect_platform(url, platform):
    assert detect_platform(url) == platform


def test_detect_platform_rejects_unknown_hosts():
    with pytest.raises(VidFlowError):
        detect_platform("https://example.com/video")

