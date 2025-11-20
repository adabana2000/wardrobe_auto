"""
Tests for image processing modules
"""

import pytest
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import tempfile
import os

# MLモジュールをインポート
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "ml"))

from ml.image_processing.detector import ClothingDetector
from ml.image_processing.embedder import ImageEmbedder
from ml.image_processing.background_remover import BackgroundRemover
from ml.image_processing.attribute_extractor import AttributeExtractor


@pytest.fixture
def sample_image():
    """テスト用サンプル画像を作成"""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        # 100x100の白い画像を作成
        img = Image.new("RGB", (100, 100), color="white")
        img.save(tmp.name)
        yield tmp.name
    # クリーンアップ
    if os.path.exists(tmp.name):
        os.remove(tmp.name)


@pytest.mark.unit
def test_detector_initialization():
    """ClothingDetectorの初期化テスト"""
    detector = ClothingDetector()
    assert detector is not None
    assert detector.model_path == "yolov8n.pt"


@pytest.mark.unit
def test_detector_fallback_detection(sample_image):
    """Detectorのフォールバック検出テスト"""
    detector = ClothingDetector()
    result = detector.detect(sample_image)

    assert "detected" in result
    assert "category" in result
    # フォールバックの場合でもカテゴリが返される
    assert result["category"] in [
        "トップス",
        "ボトムス",
        "アウター",
        "ワンピース",
        "バッグ",
    ]


@pytest.mark.unit
def test_detector_category_mapping():
    """YOLOクラスからカテゴリへのマッピングテスト"""
    detector = ClothingDetector()

    # デフォルトマッピング
    category = detector._map_yolo_class_to_clothing(0)
    assert isinstance(category, str)


@pytest.mark.unit
def test_embedder_initialization():
    """ImageEmbedderの初期化テスト"""
    embedder = ImageEmbedder()
    assert embedder is not None
    assert embedder.model_name == "openai/clip-vit-base-patch32"


@pytest.mark.unit
def test_embedder_fallback_embedding(sample_image):
    """Embedderのフォールバック埋め込みテスト"""
    embedder = ImageEmbedder()
    embedding = embedder.embed(sample_image)

    # フォールバックの場合でもベクトルが返される
    assert isinstance(embedding, np.ndarray)
    assert len(embedding) == 512  # デフォルト次元数
    # 正規化されている
    assert np.abs(np.linalg.norm(embedding) - 1.0) < 0.01


@pytest.mark.unit
def test_embedder_batch_embed(sample_image):
    """バッチ埋め込みテスト"""
    embedder = ImageEmbedder()
    embeddings = embedder.batch_embed([sample_image, sample_image])

    assert embeddings.shape == (2, 512)


@pytest.mark.unit
def test_embedder_find_similar():
    """類似ベクトル検索テスト"""
    embedder = ImageEmbedder()

    query = np.random.randn(512).astype(np.float32)
    query = query / np.linalg.norm(query)

    candidates = np.random.randn(10, 512).astype(np.float32)
    candidates = candidates / np.linalg.norm(candidates, axis=1, keepdims=True)

    results = embedder.find_similar(query, candidates, top_k=3)

    assert len(results) == 3
    assert all(isinstance(idx, int) for idx, _ in results)
    assert all(isinstance(sim, float) for _, sim in results)


@pytest.mark.unit
def test_background_remover_initialization():
    """BackgroundRemoverの初期化テスト"""
    bg_remover = BackgroundRemover()
    assert bg_remover is not None


@pytest.mark.unit
def test_background_remover_availability_check():
    """背景除去の利用可能性チェック"""
    bg_remover = BackgroundRemover()
    # rembgが利用できない場合はFalse
    assert isinstance(bg_remover.available, bool)


@pytest.mark.unit
def test_background_remover_fallback(sample_image):
    """背景除去のフォールバックテスト"""
    bg_remover = BackgroundRemover()
    result_path = bg_remover.remove_background(sample_image)

    # rembgが利用できない場合は元の画像パスが返される
    assert result_path is not None
    assert isinstance(result_path, str)


@pytest.mark.unit
def test_attribute_extractor_initialization():
    """AttributeExtractorの初期化テスト"""
    extractor = AttributeExtractor()
    assert extractor is not None
    assert extractor.embedder is None


@pytest.mark.unit
def test_attribute_extractor_with_embedder():
    """Embedder付きAttributeExtractorテスト"""
    embedder = ImageEmbedder()
    extractor = AttributeExtractor(embedder=embedder)
    assert extractor.embedder is not None


@pytest.mark.unit
def test_extract_colors(sample_image):
    """色抽出テスト"""
    extractor = AttributeExtractor()
    primary, secondary = extractor.extract_colors(sample_image)

    # 色名が返される（Noneの場合もある）
    if primary:
        assert isinstance(primary, str)
    if secondary:
        assert isinstance(secondary, str)


@pytest.mark.unit
def test_rgb_to_color_name():
    """RGB→色名変換テスト"""
    extractor = AttributeExtractor()

    # 白
    assert extractor._rgb_to_color_name((255, 255, 255)) == "白"

    # 黒
    assert extractor._rgb_to_color_name((0, 0, 0)) == "黒"

    # 赤
    color = extractor._rgb_to_color_name((255, 0, 0))
    assert color in ["赤", "ピンク", "オレンジ"]  # 近い色が選ばれる


@pytest.mark.unit
def test_extract_pattern_without_embedder(sample_image):
    """Embedderなしでのパターン抽出テスト"""
    extractor = AttributeExtractor()
    pattern = extractor.extract_pattern(sample_image)

    # Embedderがない場合はデフォルト値
    assert pattern == "無地"


@pytest.mark.unit
def test_extract_all_attributes(sample_image):
    """全属性抽出テスト"""
    extractor = AttributeExtractor()
    attributes = extractor.extract_all_attributes(sample_image)

    assert "color_primary" in attributes
    assert "color_secondary" in attributes
    assert "pattern" in attributes
    assert "material" in attributes
    assert "season_tags" in attributes
    assert "style_tags" in attributes

    # season_tagsとstyle_tagsはリスト
    assert isinstance(attributes["season_tags"], list)
    assert isinstance(attributes["style_tags"], list)
