"""
衣類検出モジュール
YOLOv8を使用した衣類検出
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# 衣類カテゴリマッピング
CLOTHING_CATEGORIES = {
    0: "トップス",
    1: "ボトムス",
    2: "アウター",
    3: "ワンピース",
    4: "靴",
    5: "バッグ",
    6: "帽子",
    7: "アクセサリー",
}


class ClothingDetector:
    """
    YOLOv8を使用した衣類検出クラス
    """

    def __init__(self, model_path: str = "yolov8n.pt"):
        """
        Args:
            model_path: YOLOv8モデルのパス
        """
        self.model_path = model_path
        self.model = None
        self._load_model()

    def _load_model(self):
        """YOLOv8モデルをロード"""
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            logger.info(f"YOLOv8 model loaded from {self.model_path}")
        except ImportError:
            logger.warning(
                "ultralytics not installed. Install with: pip install ultralytics"
            )
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            self.model = None

    def detect(self, image_path: str, confidence_threshold: float = 0.5) -> Dict:
        """
        画像から衣類を検出

        Args:
            image_path: 画像ファイルのパス
            confidence_threshold: 検出の信頼度しきい値

        Returns:
            dict: 検出結果（カテゴリ、座標、信頼度等）
        """
        if not self.model:
            # モデルが利用できない場合は、デフォルト値を返す
            logger.warning("YOLOv8 model not available. Using fallback detection.")
            return self._fallback_detection(image_path)

        try:
            # 画像を読み込み
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            # YOLOv8で検出
            results = self.model(image_path, conf=confidence_threshold)

            if len(results) == 0 or len(results[0].boxes) == 0:
                logger.info("No objects detected in image")
                return {
                    "detected": False,
                    "category": None,
                    "confidence": 0.0,
                    "bbox": None,
                }

            # 最も信頼度の高い検出結果を取得
            result = results[0]
            boxes = result.boxes

            # 最も大きな検出領域（衣類と仮定）を選択
            max_area_idx = 0
            max_area = 0

            for idx, box in enumerate(boxes):
                xyxy = box.xyxy[0].cpu().numpy()
                area = (xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1])
                if area > max_area:
                    max_area = area
                    max_area_idx = idx

            best_box = boxes[max_area_idx]
            xyxy = best_box.xyxy[0].cpu().numpy()
            confidence = float(best_box.conf[0].cpu().numpy())
            class_id = int(best_box.cls[0].cpu().numpy())

            # カテゴリ推定（YOLOのクラスから衣類カテゴリへマッピング）
            category = self._map_yolo_class_to_clothing(class_id)

            return {
                "detected": True,
                "category": category,
                "confidence": confidence,
                "bbox": {
                    "x1": float(xyxy[0]),
                    "y1": float(xyxy[1]),
                    "x2": float(xyxy[2]),
                    "y2": float(xyxy[3]),
                },
                "class_id": class_id,
            }

        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return {
                "detected": False,
                "error": str(e),
                "category": None,
                "confidence": 0.0,
            }

    def _map_yolo_class_to_clothing(self, class_id: int) -> str:
        """
        YOLOのクラスIDを衣類カテゴリにマッピング

        Args:
            class_id: YOLOのクラスID

        Returns:
            str: 衣類カテゴリ
        """
        # 一般的なCOCOデータセットのクラスマッピング
        # 実際には衣類専用データセットで学習したモデルを使用することを推奨
        coco_to_clothing = {
            0: "トップス",  # person -> デフォルト
            27: "ネクタイ",
            31: "バッグ",
            32: "バッグ",
            33: "バッグ",
        }

        # デフォルトはトップスとする（衣類と判断）
        return coco_to_clothing.get(class_id, "トップス")

    def _fallback_detection(self, image_path: str) -> Dict:
        """
        フォールバック検出（モデル利用不可時）

        画像のアスペクト比などから簡易的にカテゴリを推定

        Args:
            image_path: 画像ファイルのパス

        Returns:
            dict: 簡易検出結果
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                aspect_ratio = height / width

                # アスペクト比から簡易的に推定
                if aspect_ratio > 1.5:
                    category = "ワンピース"
                elif aspect_ratio > 1.0:
                    category = "トップス"
                elif aspect_ratio < 0.7:
                    category = "バッグ"
                else:
                    category = "ボトムス"

                return {
                    "detected": True,
                    "category": category,
                    "confidence": 0.5,  # フォールバック時は低めの信頼度
                    "bbox": {"x1": 0, "y1": 0, "x2": width, "y2": height},
                    "fallback": True,
                }

        except Exception as e:
            logger.error(f"Fallback detection failed: {e}")
            return {
                "detected": False,
                "category": "トップス",  # デフォルト
                "confidence": 0.3,
                "error": str(e),
                "fallback": True,
            }

    def batch_detect(
        self, image_paths: List[str], confidence_threshold: float = 0.5
    ) -> List[Dict]:
        """
        複数画像の一括検出

        Args:
            image_paths: 画像ファイルパスのリスト
            confidence_threshold: 検出の信頼度しきい値

        Returns:
            List[Dict]: 各画像の検出結果リスト
        """
        results = []
        for image_path in image_paths:
            result = self.detect(image_path, confidence_threshold)
            results.append(result)
        return results
