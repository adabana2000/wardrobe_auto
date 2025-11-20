"""
属性抽出モジュール
画像から衣類の属性（色、パターン、素材等）を抽出
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
from PIL import Image
import numpy as np
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class AttributeExtractor:
    """
    画像から衣類属性を抽出するクラス
    """

    # 色名マッピング（RGB -> 日本語色名）
    COLOR_MAP = {
        "黒": (0, 0, 0),
        "白": (255, 255, 255),
        "グレー": (128, 128, 128),
        "赤": (255, 0, 0),
        "ピンク": (255, 192, 203),
        "オレンジ": (255, 165, 0),
        "黄色": (255, 255, 0),
        "緑": (0, 128, 0),
        "青": (0, 0, 255),
        "紺": (0, 0, 128),
        "紫": (128, 0, 128),
        "茶色": (165, 42, 42),
        "ベージュ": (245, 245, 220),
    }

    # パターンキーワード（CLIPテキスト検索用）
    PATTERN_QUERIES = [
        "無地",
        "ストライプ",
        "チェック",
        "ドット",
        "花柄",
        "幾何学模様",
        "動物柄",
    ]

    # 素材キーワード（CLIPテキスト検索用）
    MATERIAL_QUERIES = [
        "綿",
        "ポリエステル",
        "ウール",
        "シルク",
        "デニム",
        "レザー",
        "ニット",
    ]

    # 季節タグキーワード
    SEASON_QUERIES = [
        "春",
        "夏",
        "秋",
        "冬",
        "オールシーズン",
    ]

    # スタイルタグキーワード
    STYLE_QUERIES = [
        "カジュアル",
        "フォーマル",
        "ビジネス",
        "スポーツ",
        "エレガント",
    ]

    def __init__(self, embedder=None):
        """
        Args:
            embedder: ImageEmbedderインスタンス（CLIP埋め込み用）
        """
        self.embedder = embedder

    def extract_colors(
        self, image_path: str, top_k: int = 2
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        画像から主要な色を抽出

        Args:
            image_path: 画像ファイルパス
            top_k: 抽出する色の数

        Returns:
            Tuple[str, str]: (primary_color, secondary_color)
        """
        try:
            # 画像を読み込み
            image = Image.open(image_path).convert("RGB")

            # 画像をリサイズ（処理速度向上のため）
            image.thumbnail((200, 200))

            # ピクセルデータを取得
            pixels = np.array(image).reshape(-1, 3)

            # 透明部分がある場合は除外
            if image.mode == "RGBA":
                alpha = np.array(image)[:, :, 3].reshape(-1)
                pixels = pixels[alpha > 128]

            # 主要な色を抽出（K-means的な簡易手法）
            dominant_colors = self._get_dominant_colors(pixels, k=top_k)

            # RGB値を色名に変換
            color_names = [self._rgb_to_color_name(rgb) for rgb in dominant_colors]

            primary_color = color_names[0] if len(color_names) > 0 else None
            secondary_color = color_names[1] if len(color_names) > 1 else None

            logger.info(f"Extracted colors: {primary_color}, {secondary_color}")
            return primary_color, secondary_color

        except Exception as e:
            logger.error(f"Color extraction failed: {e}")
            return None, None

    def _get_dominant_colors(
        self, pixels: np.ndarray, k: int = 2
    ) -> List[Tuple[int, int, int]]:
        """
        K-means風の簡易クラスタリングで主要色を抽出

        Args:
            pixels: ピクセルデータ配列
            k: 抽出する色の数

        Returns:
            List[Tuple]: RGB値のリスト
        """
        try:
            from sklearn.cluster import KMeans

            # K-meansクラスタリング
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(pixels)

            # クラスタ中心（= 主要色）を取得
            colors = kmeans.cluster_centers_.astype(int)

            # クラスタサイズでソート（大きい順）
            labels = kmeans.labels_
            counts = Counter(labels)
            sorted_colors = [
                colors[i]
                for i, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)
            ]

            return [tuple(color) for color in sorted_colors]

        except ImportError:
            # scikit-learnが利用できない場合は、単純にピクセルの平均色を返す
            logger.warning("scikit-learn not available. Using average color.")
            avg_color = pixels.mean(axis=0).astype(int)
            return [tuple(avg_color)]

    def _rgb_to_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """
        RGB値を色名に変換（最も近い色を選択）

        Args:
            rgb: RGB値タプル

        Returns:
            str: 色名
        """
        min_distance = float("inf")
        closest_color = "不明"

        for color_name, color_rgb in self.COLOR_MAP.items():
            # ユークリッド距離を計算
            distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb, color_rgb)))

            if distance < min_distance:
                min_distance = distance
                closest_color = color_name

        return closest_color

    def extract_pattern(self, image_path: str) -> Optional[str]:
        """
        画像からパターンを抽出（CLIP使用）

        Args:
            image_path: 画像ファイルパス

        Returns:
            str: パターン名
        """
        if not self.embedder:
            logger.warning("Embedder not available. Returning default pattern.")
            return "無地"

        try:
            # CLIPでテキスト類似度を計算
            result = self.embedder.embed_with_text(image_path, self.PATTERN_QUERIES)

            if "text_similarities" in result and result["text_similarities"]:
                # 最も類似度が高いパターンを選択
                pattern = max(
                    result["text_similarities"],
                    key=result["text_similarities"].get
                )
                logger.info(f"Extracted pattern: {pattern}")
                return pattern
            else:
                return "無地"

        except Exception as e:
            logger.error(f"Pattern extraction failed: {e}")
            return "無地"

    def extract_material(self, image_path: str) -> Optional[str]:
        """
        画像から素材を推定（CLIP使用）

        Args:
            image_path: 画像ファイルパス

        Returns:
            str: 素材名
        """
        if not self.embedder:
            logger.warning("Embedder not available. Returning default material.")
            return None

        try:
            # CLIPでテキスト類似度を計算
            result = self.embedder.embed_with_text(image_path, self.MATERIAL_QUERIES)

            if "text_similarities" in result and result["text_similarities"]:
                # 最も類似度が高い素材を選択
                material = max(
                    result["text_similarities"],
                    key=result["text_similarities"].get
                )
                logger.info(f"Extracted material: {material}")
                return material
            else:
                return None

        except Exception as e:
            logger.error(f"Material extraction failed: {e}")
            return None

    def extract_season_tags(self, image_path: str, threshold: float = 0.3) -> List[str]:
        """
        画像から季節タグを抽出（CLIP使用）

        Args:
            image_path: 画像ファイルパス
            threshold: 類似度しきい値

        Returns:
            List[str]: 季節タグのリスト
        """
        if not self.embedder:
            return []

        try:
            # CLIPでテキスト類似度を計算
            result = self.embedder.embed_with_text(image_path, self.SEASON_QUERIES)

            if "text_similarities" in result and result["text_similarities"]:
                # しきい値以上の季節タグを抽出
                tags = [
                    season
                    for season, score in result["text_similarities"].items()
                    if score >= threshold
                ]
                logger.info(f"Extracted season tags: {tags}")
                return tags
            else:
                return []

        except Exception as e:
            logger.error(f"Season tag extraction failed: {e}")
            return []

    def extract_style_tags(self, image_path: str, threshold: float = 0.3) -> List[str]:
        """
        画像からスタイルタグを抽出（CLIP使用）

        Args:
            image_path: 画像ファイルパス
            threshold: 類似度しきい値

        Returns:
            List[str]: スタイルタグのリスト
        """
        if not self.embedder:
            return []

        try:
            # CLIPでテキスト類似度を計算
            result = self.embedder.embed_with_text(image_path, self.STYLE_QUERIES)

            if "text_similarities" in result and result["text_similarities"]:
                # しきい値以上のスタイルタグを抽出
                tags = [
                    style
                    for style, score in result["text_similarities"].items()
                    if score >= threshold
                ]
                logger.info(f"Extracted style tags: {tags}")
                return tags
            else:
                return []

        except Exception as e:
            logger.error(f"Style tag extraction failed: {e}")
            return []

    def extract_all_attributes(self, image_path: str) -> Dict:
        """
        画像から全属性を一括抽出

        Args:
            image_path: 画像ファイルパス

        Returns:
            Dict: 全属性を含む辞書
        """
        primary_color, secondary_color = self.extract_colors(image_path)
        pattern = self.extract_pattern(image_path)
        material = self.extract_material(image_path)
        season_tags = self.extract_season_tags(image_path)
        style_tags = self.extract_style_tags(image_path)

        return {
            "color_primary": primary_color,
            "color_secondary": secondary_color,
            "pattern": pattern,
            "material": material,
            "season_tags": season_tags,
            "style_tags": style_tags,
        }
