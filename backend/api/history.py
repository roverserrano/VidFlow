from __future__ import annotations

from fastapi import APIRouter

from backend.services.history_service import history_service

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
def list_history() -> list[dict]:
    return history_service.list()


@router.delete("/{item_id}")
def delete_history_item(item_id: str) -> dict:
    return {"deleted": history_service.delete(item_id)}

