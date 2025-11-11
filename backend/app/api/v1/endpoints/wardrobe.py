from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db

router = APIRouter()


@router.get("")
async def list_wardrobe_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    ワードローブアイテム一覧取得
    (Phase 2で実装予定)
    """
    return {
        "message": "Wardrobe list endpoint - to be implemented in Phase 2",
        "skip": skip,
        "limit": limit
    }


@router.post("")
async def create_wardrobe_item(
    db: Session = Depends(get_db)
):
    """
    ワードローブアイテム登録
    (Phase 2で実装予定)
    """
    return {
        "message": "Wardrobe item creation - to be implemented in Phase 2"
    }


@router.get("/{item_id}")
async def get_wardrobe_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    """
    ワードローブアイテム詳細取得
    (Phase 2で実装予定)
    """
    return {
        "message": "Wardrobe item detail - to be implemented in Phase 2",
        "item_id": item_id
    }
