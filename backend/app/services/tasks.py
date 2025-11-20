from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.wardrobe import WardrobeItem
import logging

# MLモジュールをインポート（PYTHONPATHで解決）
from ml.image_processing.detector import ClothingDetector
from ml.image_processing.embedder import ImageEmbedder
from ml.image_processing.background_remover import BackgroundRemover
from ml.image_processing.attribute_extractor import AttributeExtractor

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_clothing_image(self, image_path: str):
    """
    衣類画像処理タスク

    画像から衣類を検出し、属性を抽出してDBに登録

    Args:
        image_path: 画像ファイルのパス

    Returns:
        dict: 処理結果
    """
    db = SessionLocal()

    try:
        logger.info(f"Processing image: {image_path}")

        # 1. 背景除去
        bg_remover = BackgroundRemover()
        nobg_path = bg_remover.remove_background(image_path)
        logger.info(f"Background removed: {nobg_path}")

        # 2. 衣類検出（YOLO）
        detector = ClothingDetector()
        detection_result = detector.detect(nobg_path)
        logger.info(f"Detection result: {detection_result}")

        category = detection_result.get("category", "トップス")
        confidence = detection_result.get("confidence", 0.0)

        # 3. 画像埋め込み（CLIP）
        embedder = ImageEmbedder()
        embedding = embedder.embed(nobg_path)
        logger.info(f"Embedding generated, shape: {embedding.shape}")

        # 4. 属性抽出
        attr_extractor = AttributeExtractor(embedder=embedder)
        attributes = attr_extractor.extract_all_attributes(nobg_path)
        logger.info(f"Attributes extracted: {attributes}")

        # 5. データベースに登録
        item = WardrobeItem(
            image_path=nobg_path,  # 背景除去後の画像を保存
            category=category,
            color_primary=attributes.get("color_primary"),
            color_secondary=attributes.get("color_secondary"),
            pattern=attributes.get("pattern"),
            material=attributes.get("material"),
            season_tags=attributes.get("season_tags", []),
            style_tags=attributes.get("style_tags", []),
            vector_embedding=embedding.tolist(),  # NumPy配列をリストに変換
        )

        db.add(item)
        db.commit()
        db.refresh(item)

        logger.info(f"Item saved to DB: {item.id}")

        return {
            "status": "success",
            "item_id": str(item.id),
            "category": category,
            "confidence": confidence,
            "attributes": attributes,
        }

    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        db.rollback()
        return {
            "status": "error",
            "error": str(e),
            "image_path": image_path,
        }

    finally:
        db.close()


@celery_app.task
def generate_outfit_task(weather_data: dict, schedule_data: dict):
    """
    コーディネート生成タスク
    Phase 3で実装予定：LLMによるコーディネート提案
    """
    return {
        "status": "pending",
        "message": "Outfit generation to be implemented in Phase 3",
        "weather_data": weather_data,
        "schedule_data": schedule_data,
    }


@celery_app.task
def batch_process_images(image_paths: list[str]):
    """
    複数画像の一括処理タスク

    Args:
        image_paths: 画像ファイルパスのリスト

    Returns:
        dict: 処理結果のリスト
    """
    results = []
    for image_path in image_paths:
        result = process_clothing_image.delay(image_path)
        results.append({"image_path": image_path, "task_id": result.id})

    return {
        "status": "batch_submitted",
        "total": len(image_paths),
        "tasks": results,
    }
