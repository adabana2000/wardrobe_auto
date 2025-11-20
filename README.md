# Wardrobe Auto - AI衣装管理・コーディネート自動化システム

AIを活用した衣装管理とコーディネート自動提案システムです。ローカルLLMを使用し、プライバシーを保護しながら高度な提案を実現します。

## 概要

手持ちの衣類を画像認識で自動管理し、天候・予定に応じた最適なコーディネートを提案します。

### 主要機能

1. **ワードローブ管理** - 画像認識による衣類の自動分類・管理
2. **AIコーディネート** - 天候・予定を考慮した最適なコーディネート提案
3. **購入支援** - 不足アイテムの分析とEC検索連携

## 技術スタック

### バックエンド
- **FastAPI** - メインAPI
- **PostgreSQL + pgvector** - ベクトル検索対応データベース
- **Redis** - キャッシュ/タスクキュー
- **Celery** - バックグラウンドタスク処理

### AI/ML
- **YOLOv8** - 衣類検出
- **CLIP** - 画像ベクトル化
- **rembg** - 背景除去
- **ローカルLLM** - Llama 3.2 Vision / Qwen2-VL (量子化)
- **vLLM** - 高速推論エンジン

### フロントエンド
- **Next.js 14** - React App Router
- **Tailwind CSS** - スタイリング
- **TypeScript** - 型安全性

### インフラ
- **Docker Compose** - コンテナオーケストレーション

## プロジェクト構造

```
wardrobe_auto/
├── backend/              # FastAPI バックエンド
│   ├── app/
│   │   ├── api/         # APIエンドポイント
│   │   ├── core/        # 設定・データベース
│   │   ├── models/      # DBモデル
│   │   ├── schemas/     # Pydanticスキーマ
│   │   └── services/    # ビジネスロジック
│   ├── alembic/         # DBマイグレーション
│   └── requirements.txt
├── frontend/            # Next.js フロントエンド
│   ├── app/            # App Router
│   └── components/     # Reactコンポーネント
├── ml/                  # AI/ML処理
│   ├── image_processing/ # YOLO, CLIP, rembg
│   ├── llm/            # LLM統合
│   └── models/         # モデルファイル
├── docker-compose.yml
└── README.md
```

## セットアップ

### 必要要件

**推奨構成:**
- GPU: RTX 3090/4090 または Tesla P100 x2
- RAM: 32GB以上
- Storage: NVMe SSD 500GB

**最小構成:**
- GPU: RTX 3060 12GB
- RAM: 16GB
- Storage: SSD 256GB

### インストール手順

1. **リポジトリのクローン**
```bash
git clone https://github.com/adabana2000/wardrobe_auto.git
cd wardrobe_auto
```

2. **環境変数の設定**
```bash
cp .env.example .env
# .envファイルを編集して必要な値を設定
```

3. **Dockerコンテナの起動**
```bash
docker-compose up -d
```

4. **データベースマイグレーション**
```bash
docker-compose exec backend alembic upgrade head
```

5. **フロントエンドの起動確認**
```
http://localhost:3000 にアクセス
```

6. **APIドキュメント**
```
http://localhost:8000/docs にアクセス
```

## 開発コマンド

### バックエンド

```bash
# バックエンドのログ確認
docker-compose logs -f backend

# マイグレーション作成
docker-compose exec backend alembic revision --autogenerate -m "migration message"

# マイグレーション実行
docker-compose exec backend alembic upgrade head

# バックエンドシェル
docker-compose exec backend bash
```

### フロントエンド

```bash
# フロントエンドのログ確認
docker-compose logs -f frontend

# 依存関係の追加
docker-compose exec frontend npm install <package-name>

# フロントエンドシェル
docker-compose exec frontend sh
```

### データベース

```bash
# PostgreSQLシェル
docker-compose exec postgres psql -U wardrobe -d wardrobe_db

# Redisシェル
docker-compose exec redis redis-cli
```

## 開発フェーズ

### ✅ Phase 1: 基盤構築（Week 1-2）- 完了
- ✓ Docker環境セットアップ
- ✓ PostgreSQL + pgvector データベース
- ✓ FastAPI バックエンドAPI
- ✓ Next.js フロントエンド基本構造

### ✅ Phase 2: 画像処理（Week 3-4）- 完了
- ✓ 画像アップロードAPI実装
- ✓ YOLOv8による衣類検出（フォールバック対応）
- ✓ CLIP画像埋め込み（512次元ベクトル）
- ✓ rembg背景除去機能
- ✓ 属性抽出（色・パターン・素材・季節・スタイル）
- ✓ Celeryバックグラウンドタスク処理
- ✓ DB自動登録機能

### ✅ Phase 3: LLM統合（Week 5-6）- 完了
- ✓ vLLMサーバー統合（OpenAI API互換）
- ✓ プロンプトエンジニアリング実装
- ✓ コーディネート生成ロジック
- ✓ ルールベースフォールバック
- ✓ コーディネートスコアリングエンジン

### ✅ Phase 4: 外部連携・分析（Week 7-8）- 完了
- ✓ OpenWeatherMap API統合
- ✓ 天気に基づく衣類推奨
- ✓ ワードローブギャップ分析
- ✓ 基本アイテムチェック
- ✓ 季節・スタイル別カバレッジ分析
- ✓ 組み合わせ可能性計算

### 🚧 Phase 5: UI/UX（Week 9-10）- 一部実装済み
- ✓ ホームページ更新
- [ ] ワードローブ管理画面（詳細）
- [ ] コーディネート表示画面
- [ ] 画像アップロードUI
- [ ] 分析結果表示画面
- [ ] 通知システム
- [ ] PWA対応

## API仕様

### エンドポイント

```
GET  /                          - ルート
GET  /health                    - ヘルスチェック
GET  /api/v1/health             - 詳細ヘルスチェック（DB/Redis接続確認）

# ワードローブ管理
GET  /api/v1/wardrobe           - ワードローブ一覧取得
POST /api/v1/wardrobe           - ワードローブアイテム手動登録
POST /api/v1/wardrobe/upload    - 画像アップロード（AI処理）
GET  /api/v1/wardrobe/{id}      - ワードローブアイテム詳細
PUT  /api/v1/wardrobe/{id}      - ワードローブアイテム更新
DELETE /api/v1/wardrobe/{id}    - ワードローブアイテム削除
POST /api/v1/wardrobe/{id}/wear - 着用記録

# コーディネート
GET  /api/v1/outfits            - コーディネート一覧
POST /api/v1/outfits            - コーディネート登録
GET  /api/v1/outfits/{id}       - コーディネート詳細
DELETE /api/v1/outfits/{id}     - コーディネート削除
POST /api/v1/outfits/generate   - AIコーディネート生成
PUT  /api/v1/outfits/{id}/rating - コーディネート評価
```

## データベーススキーマ

### wardrobeテーブル
- 衣類の基本情報（カテゴリ、色、素材、ブランド等）
- 着用履歴（last_worn、wear_count）
- 季節/スタイルタグ
- CLIP埋め込みベクトル（768次元）

### outfitsテーブル
- コーディネート履歴
- 天気・予定情報
- ユーザー評価

### weather_cacheテーブル
- 天気情報のキャッシュ

## セキュリティ・プライバシー

- 全データローカル保存（外部サーバーへの送信なし）
- API通信はTLS暗号化
- 画像データは暗号化ストレージ
- ユーザー認証: Authelia/Keycloak（将来実装）

## ライセンス

MIT License

## コントリビューション

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 参考資料

- [仕様書](仕様書.txt) - システムの詳細仕様
- [CLAUDE.md](CLAUDE.md) - Claude Code用のプロジェクトガイド
