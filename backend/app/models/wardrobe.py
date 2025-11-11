from sqlalchemy import Column, String, Integer, Date, ARRAY, Text, Float
from sqlalchemy.dialects.postgresql import UUID, VECTOR
import uuid
from datetime import date
from app.core.database import Base


class WardrobeItem(Base):
    __tablename__ = "wardrobe"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_path = Column(Text, nullable=False)

    # 衣類属性
    category = Column(String(50), nullable=False)  # トップス、ボトムス、アウター等
    color_primary = Column(String(30))
    color_secondary = Column(String(30))
    pattern = Column(String(50))  # 無地、ストライプ、チェック等
    material = Column(String(100))  # 綿、ポリエステル等
    brand = Column(String(100))

    # 購入・着用履歴
    purchase_date = Column(Date)
    last_worn = Column(Date)
    wear_count = Column(Integer, default=0)

    # タグ
    season_tags = Column(ARRAY(Text))  # ['春', '夏']
    style_tags = Column(ARRAY(Text))  # ['カジュアル', 'フォーマル']

    # お手入れ情報
    care_instructions = Column(Text)

    # ベクトル埋め込み (CLIP embedding - 768次元)
    # pgvector拡張が必要
    vector_embedding = Column(VECTOR(768))

    def __repr__(self):
        return f"<WardrobeItem {self.id} - {self.category}>"


class Outfit(Base):
    __tablename__ = "outfits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(Date, default=date.today)
    worn_date = Column(Date)

    # コーディネートアイテムのID配列
    item_ids = Column(ARRAY(UUID(as_uuid=True)))

    # その日の天気・予定
    weather_temp = Column(Float)
    weather_condition = Column(String(50))
    occasion = Column(String(100))

    # ユーザー評価
    user_rating = Column(Integer)  # 1-5
    notes = Column(Text)

    def __repr__(self):
        return f"<Outfit {self.id} - {self.worn_date}>"


class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False, unique=True)
    temperature = Column(Float)
    condition = Column(String(50))
    humidity = Column(Integer)
    wind_speed = Column(Float)
    raw_data = Column(Text)  # JSON文字列として保存

    def __repr__(self):
        return f"<WeatherCache {self.date} - {self.condition}>"
