from datetime import datetime

from backend.utils.filenames import build_download_basename, sanitize_title


def test_sanitize_title_keeps_cross_platform_filename_safe():
    assert sanitize_title("Mi video: prueba / final!") == "mi_video_prueba_final"
    assert sanitize_title("CON") == "con_video"


def test_build_download_basename_uses_title_resolution_and_timestamp():
    now = datetime(2024, 3, 15, 9, 30, 4)

    assert build_download_basename("Mi video", "1080p", now=now) == "mi_video_1080p_20240315_093004"

