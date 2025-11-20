"""
画像埋め込みモジュール
CLIPを使用した画像のベクトル化
"""

from typing import List, Optional, Union
from pathlib import Path
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageEmbedder:
    """
    CLIPを使用した画像埋め込みクラス
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Args:
            model_name: CLIPモデル名
        """
        self.model_name = model_name
        self.model = None
        self.processor = None
        self._load_model()

    def _load_model(self):
        """CLIPモデルをロード"""
        try:
            from transformers import CLIPProcessor, CLIPModel
            import torch

            self.model = CLIPModel.from_pretrained(self.model_name)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)

            # GPUが利用可能な場合はGPUを使用
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = self.model.to(self.device)
            self.model.eval()

            logger.info(f"CLIP model loaded: {self.model_name} on {self.device}")

        except ImportError:
            logger.warning(
                "transformers or torch not installed. "
                "Install with: pip install transformers torch"
            )
            self.model = None
            self.processor = None
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            self.model = None
            self.processor = None

    def embed(self, image_path: str) -> np.ndarray:
        """
        画像をベクトルに変換

        Args:
            image_path: 画像ファイルのパス

        Returns:
            np.ndarray: 512次元のベクトル埋め込み（CLIP ViT-B/32の場合）
            モデルが利用できない場合はランダムベクトルを返す
        """
        if not self.model or not self.processor:
            logger.warning("CLIP model not available. Using random embedding.")
            return self._fallback_embedding()

        try:
            import torch

            # 画像を読み込み
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            image = Image.open(image_path).convert("RGB")

            # 画像を前処理
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 推論実行（勾配計算なし）
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)

            # 正規化
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)

            # NumPy配列に変換
            embedding = image_features.cpu().numpy().flatten()

            logger.info(f"Generated embedding of shape {embedding.shape}")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return self._fallback_embedding()

    def embed_with_text(
        self, image_path: str, text_queries: List[str]
    ) -> dict:
        """
        画像とテキストの類似度を計算

        Args:
            image_path: 画像ファイルのパス
            text_queries: テキストクエリのリスト

        Returns:
            dict: 画像埋め込みと各テキストとの類似度
        """
        if not self.model or not self.processor:
            logger.warning("CLIP model not available.")
            return {
                "image_embedding": self._fallback_embedding(),
                "text_similarities": {},
            }

        try:
            import torch

            # 画像を読み込み
            image = Image.open(image_path).convert("RGB")

            # 画像とテキストを前処理
            inputs = self.processor(
                text=text_queries,
                images=image,
                return_tensors="pt",
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 推論実行
            with torch.no_grad():
                outputs = self.model(**inputs)
                image_features = outputs.image_embeds
                text_features = outputs.text_embeds

            # 正規化
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)

            # 類似度計算（コサイン類似度）
            similarities = (image_features @ text_features.T).cpu().numpy()[0]

            # 結果を辞書形式で返す
            text_similarities = {
                query: float(sim)
                for query, sim in zip(text_queries, similarities)
            }

            return {
                "image_embedding": image_features.cpu().numpy().flatten(),
                "text_similarities": text_similarities,
            }

        except Exception as e:
            logger.error(f"Text similarity calculation failed: {e}")
            return {
                "image_embedding": self._fallback_embedding(),
                "text_similarities": {},
                "error": str(e),
            }

    def _fallback_embedding(self, dim: int = 512) -> np.ndarray:
        """
        フォールバック埋め込み（モデル利用不可時）

        ランダムな正規化ベクトルを返す

        Args:
            dim: ベクトルの次元数

        Returns:
            np.ndarray: ランダムベクトル
        """
        # ランダムベクトルを生成して正規化
        vec = np.random.randn(dim).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        return vec

    def batch_embed(self, image_paths: List[str]) -> np.ndarray:
        """
        複数画像の一括埋め込み

        Args:
            image_paths: 画像ファイルパスのリスト

        Returns:
            np.ndarray: 埋め込みベクトルの配列 (N x D)
        """
        embeddings = []
        for image_path in image_paths:
            emb = self.embed(image_path)
            embeddings.append(emb)
        return np.array(embeddings)

    def find_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: np.ndarray,
        top_k: int = 5
    ) -> List[tuple]:
        """
        類似ベクトル検索

        Args:
            query_embedding: クエリベクトル
            candidate_embeddings: 候補ベクトルの配列
            top_k: 返す上位k件

        Returns:
            List[tuple]: (インデックス, 類似度) のリスト
        """
        # コサイン類似度計算
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        candidate_norms = candidate_embeddings / np.linalg.norm(
            candidate_embeddings, axis=1, keepdims=True
        )

        similarities = candidate_norms @ query_norm

        # 上位k件のインデックスを取得
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = [(int(idx), float(similarities[idx])) for idx in top_indices]
        return results
