from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.core.database import get_db
from app.models.wardrobe import Outfit, WardrobeItem
from app.schemas import (
    OutfitCreate,
    OutfitResponse,
    OutfitDetail,
    OutfitGenerationRequest,
    OutfitSuggestion,
    WardrobeItemResponse,
)

router = APIRouter()


@router.get("", response_model=List[OutfitResponse])
async def list_outfits(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    コーディネート一覧取得
    """
    outfits = db.query(Outfit).offset(skip).limit(limit).all()
    return outfits


@router.post("", response_model=OutfitResponse)
async def create_outfit(
    outfit: OutfitCreate,
    db: Session = Depends(get_db)
):
    """
    コーディネート手動登録

    アイテムIDのリストからコーディネートを作成
    """
    # アイテムの存在確認
    for item_id in outfit.item_ids:
        item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()
        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"Item {item_id} not found"
            )

    db_outfit = Outfit(**outfit.model_dump())
    db.add(db_outfit)
    db.commit()
    db.refresh(db_outfit)
    return db_outfit


@router.get("/{outfit_id}", response_model=OutfitDetail)
async def get_outfit(
    outfit_id: UUID,
    db: Session = Depends(get_db)
):
    """
    コーディネート詳細取得（アイテム情報含む）
    """
    outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()

    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")

    # アイテム情報取得
    items = []
    if outfit.item_ids:
        items = db.query(WardrobeItem).filter(
            WardrobeItem.id.in_(outfit.item_ids)
        ).all()

    # OutfitDetailオブジェクトを構築
    outfit_dict = {
        "id": outfit.id,
        "created_at": outfit.created_at,
        "worn_date": outfit.worn_date,
        "item_ids": outfit.item_ids,
        "weather_temp": outfit.weather_temp,
        "weather_condition": outfit.weather_condition,
        "occasion": outfit.occasion,
        "user_rating": outfit.user_rating,
        "notes": outfit.notes,
        "items": items,
    }

    return outfit_dict


@router.delete("/{outfit_id}")
async def delete_outfit(
    outfit_id: UUID,
    db: Session = Depends(get_db)
):
    """
    コーディネート削除
    """
    outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()

    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")

    db.delete(outfit)
    db.commit()

    return {"message": "Outfit deleted successfully"}


@router.post("/generate", response_model=List[OutfitSuggestion])
async def generate_outfit_suggestions(
    request: OutfitGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    AIコーディネート生成

    Phase 3で実装予定: LLMを使用した自動コーディネート生成
    """
    # Phase 3で実装
    # 現在はダミーレスポンスを返す
    return [{
        "items": [],
        "reason": "Phase 3で実装予定: LLMによる自動コーディネート生成",
        "weather_appropriateness": None,
        "style_score": None,
    }]


@router.put("/{outfit_id}/rating")
async def rate_outfit(
    outfit_id: UUID,
    rating: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    コーディネート評価

    ユーザーがコーディネートを評価（1-5）
    """
    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    outfit = db.query(Outfit).filter(Outfit.id == outfit_id).first()

    if not outfit:
        raise HTTPException(status_code=404, detail="Outfit not found")

    outfit.user_rating = rating
    if notes:
        outfit.notes = notes

    db.commit()
    db.refresh(outfit)

    return {"message": "Rating saved", "rating": rating}
