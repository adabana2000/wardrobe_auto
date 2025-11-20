"""
Pytest configuration and fixtures
"""

import pytest
import sys
from pathlib import Path

# MLモジュールのパスを追加（Docker外でのテスト用）
ml_modules_path = Path(__file__).parent.parent.parent.parent
if str(ml_modules_path) not in sys.path:
    sys.path.insert(0, str(ml_modules_path))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# テスト用のインメモリデータベース
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """テスト用データベースセッション"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """テスト用FastAPIクライアント"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_wardrobe_item():
    """サンプルワードローブアイテム"""
    return {
        "image_path": "/test/image.jpg",
        "category": "トップス",
        "color_primary": "白",
        "color_secondary": "青",
        "pattern": "ストライプ",
        "material": "綿",
        "season_tags": ["春", "夏"],
        "style_tags": ["カジュアル"],
    }


@pytest.fixture
def sample_outfit():
    """サンプルコーディネート"""
    return {
        "item_ids": [],
        "weather_temp": 20.0,
        "weather_condition": "晴れ",
        "occasion": "カジュアル外出",
    }
