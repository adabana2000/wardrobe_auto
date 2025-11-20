"""
Tests for outfits API endpoints
"""

import pytest
from uuid import uuid4


@pytest.mark.unit
def test_list_outfits_empty(client):
    """空のコーディネート一覧取得"""
    response = client.get("/api/v1/outfits")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.unit
def test_create_outfit(client, sample_wardrobe_item, sample_outfit):
    """コーディネート作成テスト"""
    # ワードローブアイテムを作成
    item1_response = client.post("/api/v1/wardrobe", json=sample_wardrobe_item)
    item1_id = item1_response.json()["id"]

    item2 = sample_wardrobe_item.copy()
    item2["category"] = "ボトムス"
    item2_response = client.post("/api/v1/wardrobe", json=item2)
    item2_id = item2_response.json()["id"]

    # コーディネートを作成
    outfit_data = sample_outfit.copy()
    outfit_data["item_ids"] = [item1_id, item2_id]

    response = client.post("/api/v1/outfits", json=outfit_data)
    assert response.status_code == 200
    data = response.json()
    assert len(data["item_ids"]) == 2
    assert data["weather_temp"] == sample_outfit["weather_temp"]
    assert "id" in data


@pytest.mark.unit
def test_create_outfit_with_nonexistent_item(client, sample_outfit):
    """存在しないアイテムでコーディネート作成テスト"""
    outfit_data = sample_outfit.copy()
    outfit_data["item_ids"] = [str(uuid4())]

    response = client.post("/api/v1/outfits", json=outfit_data)
    assert response.status_code == 404


@pytest.mark.unit
def test_get_outfit_detail(client, sample_wardrobe_item, sample_outfit):
    """コーディネート詳細取得テスト（アイテム情報含む）"""
    # ワードローブアイテムを作成
    item_response = client.post("/api/v1/wardrobe", json=sample_wardrobe_item)
    item_id = item_response.json()["id"]

    # コーディネートを作成
    outfit_data = sample_outfit.copy()
    outfit_data["item_ids"] = [item_id]
    create_response = client.post("/api/v1/outfits", json=outfit_data)
    outfit_id = create_response.json()["id"]

    # コーディネート詳細を取得
    response = client.get(f"/api/v1/outfits/{outfit_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == outfit_id
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == item_id


@pytest.mark.unit
def test_delete_outfit(client, sample_wardrobe_item, sample_outfit):
    """コーディネート削除テスト"""
    # ワードローブアイテムを作成
    item_response = client.post("/api/v1/wardrobe", json=sample_wardrobe_item)
    item_id = item_response.json()["id"]

    # コーディネートを作成
    outfit_data = sample_outfit.copy()
    outfit_data["item_ids"] = [item_id]
    create_response = client.post("/api/v1/outfits", json=outfit_data)
    outfit_id = create_response.json()["id"]

    # コーディネートを削除
    response = client.delete(f"/api/v1/outfits/{outfit_id}")
    assert response.status_code == 200

    # 削除されたことを確認
    get_response = client.get(f"/api/v1/outfits/{outfit_id}")
    assert get_response.status_code == 404


@pytest.mark.unit
def test_rate_outfit(client, sample_wardrobe_item, sample_outfit):
    """コーディネート評価テスト"""
    # ワードローブアイテムを作成
    item_response = client.post("/api/v1/wardrobe", json=sample_wardrobe_item)
    item_id = item_response.json()["id"]

    # コーディネートを作成
    outfit_data = sample_outfit.copy()
    outfit_data["item_ids"] = [item_id]
    create_response = client.post("/api/v1/outfits", json=outfit_data)
    outfit_id = create_response.json()["id"]

    # 評価を追加
    response = client.put(
        f"/api/v1/outfits/{outfit_id}/rating",
        params={"rating": 5, "notes": "とても良い"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 5


@pytest.mark.unit
def test_rate_outfit_invalid_rating(client, sample_wardrobe_item, sample_outfit):
    """無効な評価値テスト"""
    # ワードローブアイテムを作成
    item_response = client.post("/api/v1/wardrobe", json=sample_wardrobe_item)
    item_id = item_response.json()["id"]

    # コーディネートを作成
    outfit_data = sample_outfit.copy()
    outfit_data["item_ids"] = [item_id]
    create_response = client.post("/api/v1/outfits", json=outfit_data)
    outfit_id = create_response.json()["id"]

    # 無効な評価値（範囲外）
    response = client.put(
        f"/api/v1/outfits/{outfit_id}/rating",
        params={"rating": 10},
    )
    assert response.status_code == 400


@pytest.mark.unit
def test_generate_outfit_suggestions(client):
    """AIコーディネート生成テスト（ダミーレスポンス）"""
    request_data = {
        "occasion": "カジュアル外出",
        "style_preference": "カジュアル",
    }

    response = client.post("/api/v1/outfits/generate", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
