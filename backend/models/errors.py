from __future__ import annotations


class VidFlowError(Exception):
    def __init__(self, message: str, *, code: str = "vidflow_error", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def humanize_download_error(error: Exception | str) -> str:
    text = str(error)
    lowered = text.lower()

    if "unsupported url" in lowered or "no suitable extractor" in lowered:
        return "URL no valida o plataforma no soportada."
    if "private video" in lowered or "login" in lowered or "sign in" in lowered:
        return "El video no esta disponible publicamente."
    if "not available in your country" in lowered or "region" in lowered:
        return "Video no disponible en tu region."
    if "network" in lowered or "timed out" in lowered or "connection" in lowered:
        return "Sin conexion a internet o la plataforma no responde."
    if "ffmpeg" in lowered:
        return "Error al procesar el archivo con ffmpeg."
    if "requested format is not available" in lowered:
        return "La calidad seleccionada ya no esta disponible."

    return text.strip() or "No se pudo completar la operacion."

