from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.core.database import get_db
from app.models.wardrobe import WardrobeItem
from app.schemas import (
    WardrobeItemCreate,
    WardrobeItemUpdate,
    WardrobeItemResponse,
    WardrobeItemDetail,
    ImageUploadResponse,
)
from app.services.tasks import process_clothing_image
import os
import uuid
from pathlib import Path

router = APIRouter()

# 画像保存先ディレクトリ
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("", response_model=List[WardrobeItemResponse])
async def list_wardrobe_items(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    ワードローブアイテム一覧取得

    Args:
        skip: スキップ数
        limit: 取得数上限
        category: カテゴリでフィルタ
        season: 季節でフィルタ
    """
    query = db.query(WardrobeItem)

    if category:
        query = query.filter(WardrobeItem.category == category)

    if season:
        query = query.filter(WardrobeItem.season_tags.contains([season]))

    items = query.offset(skip).limit(limit).all()
    return items


@router.post("", response_model=WardrobeItemResponse)
async def create_wardrobe_item(
    item: WardrobeItemCreate,
    db: Session = Depends(get_db)
):
    """
    ワードローブアイテム手動登録

    画像処理を経ずに手動でアイテムを登録する場合に使用
    """
    db_item = WardrobeItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.post("/upload", response_model=ImageUploadResponse)
async def upload_clothing_image(
    file: UploadFile = File(..., description="衣類画像ファイル"),
    db: Session = Depends(get_db)
):
    """
    衣類画像アップロード

    アップロードされた画像をバックグラウンドで処理し、
    自動的に属性を抽出してDBに登録します
    """
    # ファイル拡張子チェック
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Allowed: {allowed_extensions}"
        )

    # ユニークなファイル名生成
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    filepath = UPLOAD_DIR / filename

    # ファイル保存
    try:
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Celeryタスクとして画像処理を実行
    task = process_clothing_image.delay(str(filepath))

    return ImageUploadResponse(
        task_id=task.id,
        message="Image uploaded successfully. Processing in background."
    )


@router.get("/{item_id}", response_model=WardrobeItemDetail)
async def get_wardrobe_item(
    item_id: UUID,
    db: Session = Depends(get_db)
):
    """
    ワードローブアイテム詳細取得
    """
    item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


@router.put("/{item_id}", response_model=WardrobeItemResponse)
async def update_wardrobe_item(
    item_id: UUID,
    item_update: WardrobeItemUpdate,
    db: Session = Depends(get_db)
):
    """
    ワードローブアイテム更新
    """
    db_item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # 更新
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
async def delete_wardrobe_item(
    item_id: UUID,
    db: Session = Depends(get_db)
):
    """
    ワードローブアイテム削除
    """
    db_item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # 画像ファイルも削除
    if db_item.image_path and os.path.exists(db_item.image_path):
        try:
            os.remove(db_item.image_path)
        except Exception as e:
            print(f"Failed to delete image file: {e}")

    db.delete(db_item)
    db.commit()

    return {"message": "Item deleted successfully"}


@router.post("/{item_id}/wear")
async def record_wear(
    item_id: UUID,
    worn_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    着用記録

    アイテムを着用した記録を残す
    """
    db_item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    db_item.last_worn = worn_date or date.today()
    db_item.wear_count = (db_item.wear_count or 0) + 1

    db.commit()
    db.refresh(db_item)

    return {"message": "Wear recorded", "wear_count": db_item.wear_count}
