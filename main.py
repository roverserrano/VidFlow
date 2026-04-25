from __future__ import annotations

import uvicorn

from backend.config import backend_host, backend_port


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=backend_host(), port=backend_port(), reload=False)
