# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

AI衣装管理・コーディネート自動化システム - ローカルLLMを活用し、手持ちの衣類を管理して天候・予定に応じた最適なコーディネートを自動提案するシステム。

## アーキテクチャ

### 3層構造

1. **ワードローブ管理層**
   - 画像認識AI (YOLO/ViT) による衣類の自動分類
   - PostgreSQL + pgvector によるベクトル検索対応DB
   - CLIP埋め込みによる視覚的類似検索

2. **インテリジェンス層**
   - ローカルLLM (Llama 3.2 Vision 11B または Qwen2-VL-7B)
   - vLLMサーバーによる高速推論
   - コーディネートルールエンジン（カラー理論、季節適合性、フォーマル度）

3. **外部連携層**
   - OpenWeatherMap API - 天気情報取得
   - CalDAV/Google Calendar - スケジュール連携
   - 楽天/Amazon API - 不足アイテムのEC検索

### 技術スタック

**バックエンド:**
- FastAPI - メインAPI
- Celery - バックグラウンドタスク処理
- Redis - キャッシュ/タスクキュー
- PostgreSQL + pgvector拡張

**AI/ML:**
- YOLOv8 - 衣類検出
- CLIP - 画像ベクトル化
- rembg - 背景除去
- vLLM - LLM推論エンジン
- 量子化: GGUF/AWQ形式

**フロントエンド:**
- Next.js 14 (App Router)
- Tailwind CSS + shadcn/ui
- PWA対応

## データベーススキーマ

`wardrobe`テーブル:
- 衣類の属性（カテゴリ、色、素材、ブランド等）
- 着用履歴（last_worn、wear_count）
- 季節/スタイルタグ
- CLIP埋め込みベクトル (768次元)

## 画像処理パイプライン

撮影 → 背景除去(rembg) → 衣類検出(YOLOv8) → 属性抽出 → ベクトル化(CLIP) → DB登録

重要な属性抽出項目:
- カテゴリ分類（トップス/ボトムス/アウター等）
- カラー分析（primary/secondary色）
- パターン認識
- 素材推定
- ブランド抽出（OCR）
- 季節適性判定

## コーディネート生成ロジック

LLMへのコンテキスト:
- 天気情報（気温、天候、湿度）
- スケジュール（時間、イベント種別）
- 利用可能な衣類データ
- 最近7日間の着用履歴

考慮要素:
- TPO（Time, Place, Occasion）
- カラーコーディネート理論（補色/類似色）
- 着回し頻度の最適化
- シーズン適合性

## ワードローブギャップ分析

システムが自動分析する項目:
- 基本アイテムの充足度
- スタイル別カバレッジ
- 季節別アイテム充足度
- コーディネート組み合わせ可能性スコア

## ハードウェア要件

**推奨構成:**
- GPU: RTX 3090/4090 または Tesla P100 x2
- RAM: 32GB以上
- Storage: NVMe SSD 500GB

**最小構成:**
- GPU: RTX 3060 12GB
- RAM: 16GB
- Storage: SSD 256GB

## セキュリティ・プライバシー

- 全データローカル保存（外部サーバーへの送信なし）
- API通信はTLS暗号化必須
- 画像データは暗号化ストレージ
- ユーザー認証: Authelia/Keycloak使用予定

## 実装フェーズ

1. **Phase 1 (Week 1-4)**: 基盤構築・画像処理パイプライン
2. **Phase 2 (Week 5-6)**: LLM統合・コーディネート生成
3. **Phase 3 (Week 7-8)**: 外部API連携・ギャップ分析
4. **Phase 4 (Week 9-10)**: UI/UX・通知システム

## 将来の拡張機能

- SNSトレンド分析（Instagram/Pinterest連携）
- 3Dバーチャル試着（CLO3D/Marvelous Designer）
- サステナビリティ分析（CO2フットプリント計算）
- 共有ワードローブ（家族間での服の共有管理）
