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
from sqlalchemy import create_engine, event, TypeDecorator, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.dialects import sqlite
import uuid

from app.main import app
from app.core.database import Base, get_db

# SQLite用のUUID型デコレータ
class SQLiteUUID(TypeDecorator):
    """SQLiteでUUIDを文字列として保存"""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value

# SQLiteTypeCompilerにvisit_UUIDとvisit_ARRAYメソッドを追加
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

def visit_UUID(self, type_, **kw):
    """SQLiteでUUID型をTEXTとしてコンパイル"""
    return "TEXT"

def visit_ARRAY(self, type_, **kw):
    """SQLiteでARRAY型をTEXT(JSON文字列)としてコンパイル"""
    return "TEXT"

def visit_VECTOR(self, type_, **kw):
    """SQLiteでVector型をTEXT(JSON文字列)としてコンパイル"""
    return "TEXT"

# メソッドを動的に追加
SQLiteTypeCompiler.visit_UUID = visit_UUID
SQLiteTypeCompiler.visit_ARRAY = visit_ARRAY
SQLiteTypeCompiler.visit_VECTOR = visit_VECTOR

# テスト用のインメモリデータベース
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# UUIDをSQLiteで扱うためのイベントリスナー
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """SQLite接続時の設定"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# UUIDパラメータを文字列に、ARRAY/VECTORをJSON文字列に変換
@event.listens_for(engine, "before_cursor_execute", retval=True)
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    """UUID、ARRAY、Vector値を変換"""
    import json
    import numpy as np

    def convert_value(value):
        """値を適切な形式に変換"""
        if isinstance(value, uuid.UUID):
            return str(value)
        elif isinstance(value, list):
            # リストの場合、JSON文字列に変換
            if value and isinstance(value[0], uuid.UUID):
                # UUIDのリスト
                return json.dumps([str(v) for v in value])
            else:
                # 通常のリスト（タグなど）
                return json.dumps(value)
        elif isinstance(value, np.ndarray):
            # numpyベクトルの場合、JSON文字列に変換
            return json.dumps(value.tolist())
        return value

    if isinstance(params, dict):
        new_params = {}
        for key, value in params.items():
            new_params[key] = convert_value(value)
        return statement, new_params
    elif isinstance(params, (list, tuple)):
        new_params = []
        for value in params:
            new_params.append(convert_value(value))
        return statement, tuple(new_params) if isinstance(params, tuple) else new_params
    return statement, params

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
