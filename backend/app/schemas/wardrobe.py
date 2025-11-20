from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from uuid import UUID


class WardrobeItemBase(BaseModel):
    """ワードローブアイテムの基本スキーマ"""
    category: str = Field(..., description="カテゴリ（トップス、ボトムス、アウター等）")
    color_primary: Optional[str] = Field(None, description="メインカラー")
    color_secondary: Optional[str] = Field(None, description="サブカラー")
    pattern: Optional[str] = Field(None, description="パターン（無地、ストライプ、チェック等）")
    material: Optional[str] = Field(None, description="素材（綿、ポリエステル等）")
    brand: Optional[str] = Field(None, description="ブランド名")
    purchase_date: Optional[date] = Field(None, description="購入日")
    season_tags: Optional[List[str]] = Field(default_factory=list, description="季節タグ")
    style_tags: Optional[List[str]] = Field(default_factory=list, description="スタイルタグ")
    care_instructions: Optional[str] = Field(None, description="お手入れ方法")


class WardrobeItemCreate(WardrobeItemBase):
    """ワードローブアイテム作成用スキーマ"""
    image_path: str = Field(..., description="画像ファイルパス")


class WardrobeItemUpdate(BaseModel):
    """ワードローブアイテム更新用スキーマ"""
    category: Optional[str] = None
    color_primary: Optional[str] = None
    color_secondary: Optional[str] = None
    pattern: Optional[str] = None
    material: Optional[str] = None
    brand: Optional[str] = None
    purchase_date: Optional[date] = None
    last_worn: Optional[date] = None
    season_tags: Optional[List[str]] = None
    style_tags: Optional[List[str]] = None
    care_instructions: Optional[str] = None


class WardrobeItemResponse(WardrobeItemBase):
    """ワードローブアイテムレスポンス用スキーマ"""
    id: UUID
    image_path: str
    last_worn: Optional[date]
    wear_count: int

    class Config:
        from_attributes = True


class WardrobeItemDetail(WardrobeItemResponse):
    """ワードローブアイテム詳細レスポンス用スキーマ"""
    # ベクトル埋め込みは含めない（サイズが大きいため）
    pass


class ImageUploadResponse(BaseModel):
    """画像アップロードレスポンス"""
    task_id: str = Field(..., description="CeleryタスクID")
    message: str = Field(..., description="メッセージ")


class ImageProcessingResult(BaseModel):
    """画像処理結果"""
    item_id: Optional[UUID] = None
    category: Optional[str] = None
    color_primary: Optional[str] = None
    color_secondary: Optional[str] = None
    pattern: Optional[str] = None
    material: Optional[str] = None
    brand: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


class OutfitCreate(BaseModel):
    """コーディネート作成用スキーマ"""
    item_ids: List[UUID] = Field(..., description="アイテムIDのリスト")
    worn_date: Optional[date] = Field(None, description="着用日")
    weather_temp: Optional[float] = Field(None, description="気温")
    weather_condition: Optional[str] = Field(None, description="天候")
    occasion: Optional[str] = Field(None, description="予定・シーン")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="ユーザー評価 (1-5)")
    notes: Optional[str] = Field(None, description="メモ")


class OutfitResponse(BaseModel):
    """コーディネートレスポンス用スキーマ"""
    id: UUID
    created_at: date
    worn_date: Optional[date]
    item_ids: List[UUID]
    weather_temp: Optional[float]
    weather_condition: Optional[str]
    occasion: Optional[str]
    user_rating: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True


class OutfitDetail(OutfitResponse):
    """コーディネート詳細レスポンス（アイテム情報含む）"""
    items: List[WardrobeItemResponse] = Field(default_factory=list, description="コーディネートに含まれるアイテム")


class OutfitGenerationRequest(BaseModel):
    """コーディネート生成リクエスト"""
    occasion: Optional[str] = Field(None, description="予定・シーン")
    style_preference: Optional[str] = Field(None, description="スタイル指定")
    excluded_items: Optional[List[UUID]] = Field(default_factory=list, description="除外アイテム")


class OutfitSuggestion(BaseModel):
    """コーディネート提案"""
    items: List[WardrobeItemResponse]
    reason: str = Field(..., description="提案理由")
    weather_appropriateness: Optional[str] = None
    style_score: Optional[float] = None
