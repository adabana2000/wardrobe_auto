"""
Tests for wardrobe API endpoints
"""

import pytest
from uuid import uuid4


@pytest.mark.unit
def test_root_endpoint(client):
    """ルートエンドポイントのテスト"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.unit
def test_health_check(client):
    """ヘルスチェックエンドポイントのテスト"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.unit
def test_list_wardrobe_items_empty(client):
    """空のワードローブ一覧取得"""
    response = client.get("/api/v1/wardrobe")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.unit
def test_create_wardrobe_item(client, sample_wardrobe_item):
    """ワードローブアイテム作成テスト"""
    response = client.post("/api/v1/wardrobe", json=sample_wardrobe_item)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == sample_wardrobe_item["category"]
    assert data["color_primary"] == sample_wardrobe_item["color_primary"]
    assert "id" in data


@pytest.mark.unit
def test_get_wardrobe_item(client, sample_wardrobe_item):
    """ワードローブアイテム詳細取得テスト"""
    # アイテムを作成
    create_response = client.post("/api/v1/wardrobe", json=sample_wardrobe_item)
    item_id = create_response.json()["id"]

    # アイテムを取得
    response = client.get(f"/api/v1/wardrobe/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["category"] == sample_wardrobe_item["category"]


@pytest.mark.unit
def test_get_nonexistent_item(client):
    """存在しないアイテムの取得テスト"""
    fake_id = str(uuid4())
    response = client.get(f"/api/v1/wardrobe/{fake_id}")
    assert response.status_code == 404


@pytest.mark.unit
def test_update_wardrobe_item(client, sample_wardrobe_item):
    """ワードローブアイテム更新テスト"""
    # アイテムを作成
    create_response = client.post("/api/v1/wardrobe", json=sample_wardrobe_item)
    item_id = create_response.json()["id"]

    # アイテムを更新
    update_data = {"color_primary": "黒"}
    response = client.put(f"/api/v1/wardrobe/{item_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["color_primary"] == "黒"
    assert data["category"] == sample_wardrobe_item["category"]  # 他のフィールドは変更されない


@pytest.mark.unit
def test_delete_wardrobe_item(client, sample_wardrobe_item):
    """ワードローブアイテム削除テスト"""
    # アイテムを作成
    create_response = client.post("/api/v1/wardrobe", json=sample_wardrobe_item)
    item_id = create_response.json()["id"]

    # アイテムを削除
    response = client.delete(f"/api/v1/wardrobe/{item_id}")
    assert response.status_code == 200

    # 削除されたことを確認
    get_response = client.get(f"/api/v1/wardrobe/{item_id}")
    assert get_response.status_code == 404


@pytest.mark.unit
def test_record_wear(client, sample_wardrobe_item):
    """着用記録テスト"""
    # アイテムを作成
    create_response = client.post("/api/v1/wardrobe", json=sample_wardrobe_item)
    item_id = create_response.json()["id"]

    # 着用を記録
    response = client.post(f"/api/v1/wardrobe/{item_id}/wear")
    assert response.status_code == 200
    data = response.json()
    assert data["wear_count"] == 1

    # 再度着用を記録
    response = client.post(f"/api/v1/wardrobe/{item_id}/wear")
    assert response.status_code == 200
    data = response.json()
    assert data["wear_count"] == 2


@pytest.mark.unit
def test_filter_by_category(client, sample_wardrobe_item):
    """カテゴリフィルタテスト"""
    # 複数のアイテムを作成
    client.post("/api/v1/wardrobe", json=sample_wardrobe_item)

    bottoms_item = sample_wardrobe_item.copy()
    bottoms_item["category"] = "ボトムス"
    client.post("/api/v1/wardrobe", json=bottoms_item)

    # カテゴリでフィルタ
    response = client.get("/api/v1/wardrobe?category=トップス")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "トップス"


@pytest.mark.unit
def test_pagination(client, sample_wardrobe_item):
    """ページネーションテスト"""
    # 複数のアイテムを作成
    for i in range(5):
        item = sample_wardrobe_item.copy()
        item["image_path"] = f"/test/image_{i}.jpg"
        client.post("/api/v1/wardrobe", json=item)

    # ページネーション
    response = client.get("/api/v1/wardrobe?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
