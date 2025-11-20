# Tests for Wardrobe Auto Backend

このディレクトリには、Wardrobe Auto バックエンドのテストが含まれています。

## テスト構成

```
tests/
├── __init__.py
├── conftest.py              # pytest設定とフィクスチャ
├── test_api_wardrobe.py     # ワードローブAPI のテスト
├── test_api_outfits.py      # コーディネートAPI のテスト
├── test_image_processing.py # 画像処理モジュールのテスト
└── test_services.py         # サービス層のテスト
```

## テストの実行

### ローカル環境

```bash
cd backend
pip install -r requirements.txt
pytest
```

### Docker環境

```bash
docker-compose exec backend pytest
```

### カバレッジレポート付き

```bash
pytest --cov=app --cov-report=html
```

### 特定のマーカーのみ実行

```bash
# ユニットテストのみ
pytest -m unit

# 統合テストのみ
pytest -m integration
```

### 特定のテストファイルのみ実行

```bash
pytest tests/test_api_wardrobe.py
```

### 詳細な出力

```bash
pytest -v
```

## テストカバレッジ

### API エンドポイント
- ✓ ワードローブ管理 (CRUD操作、フィルタ、ページネーション)
- ✓ コーディネート管理 (作成、詳細、削除、評価)
- ✓ ヘルスチェック

### 画像処理モジュール
- ✓ ClothingDetector (YOLO衣類検出)
- ✓ ImageEmbedder (CLIP画像埋め込み)
- ✓ BackgroundRemover (背景除去)
- ✓ AttributeExtractor (属性抽出)

### サービス層
- ✓ WeatherService (天気情報取得、推奨)
- ✓ WardrobeGapAnalyzer (ギャップ分析)
- ✓ OutfitGenerator (コーディネート生成)
- ✓ OutfitRulesEngine (ルールエンジン)

## テストデータ

テストには以下のフィクスチャが使用されます：

- `db_session`: SQLiteインメモリデータベースセッション
- `client`: FastAPI TestClient
- `sample_wardrobe_item`: サンプルワードローブアイテム
- `sample_outfit`: サンプルコーディネート
- `sample_image`: テスト用画像（自動生成）

## 注意事項

### MLモジュールの依存関係

画像処理テストは、MLライブラリ（YOLO、CLIP、rembg等）がインストールされていない場合でも
フォールバック機能を使用して実行されます。

### 外部API

天気APIなどの外部サービスは、APIキーが設定されていない場合、モックデータを使用します。

### GPU

GPU依存の処理（CLIP埋め込み等）は、GPUが利用できない場合はCPUまたはフォールバック処理で実行されます。

## CI/CD

GitHub Actionsでは、以下のテストが自動実行されます：

1. ユニットテスト（全テスト）
2. コードカバレッジ計測
3. コードスタイルチェック（flake8、black）

## トラブルシューティング

### `ModuleNotFoundError`

```bash
# PYTHONPATHを設定
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### データベースエラー

テストは独立したSQLiteインメモリデータベースを使用するため、
本番DBには影響しません。

### 画像処理テストの失敗

MLライブラリがインストールされていない場合は、フォールバック処理が
正常に動作することを確認してください。
