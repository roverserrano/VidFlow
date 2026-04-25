from __future__ import annotations


def format_bytes(value: int | float | None) -> str:
    if value is None:
        return "-"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    unit = 0
    while size >= 1024 and unit < len(units) - 1:
        size /= 1024
        unit += 1

    if unit == 0:
        return f"{int(size)} {units[unit]}"
    return f"{size:.1f} {units[unit]}"


def format_speed(value: int | float | None) -> str:
    if not value:
        return "-"
    return f"{format_bytes(value)}/s"


def format_eta(value: int | float | None) -> str:
    if value is None:
        return "-"

    total = max(0, int(value))
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60

    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"


def format_duration(value: int | float | None) -> str:
    if value is None:
        return "-"
    return format_eta(value)

