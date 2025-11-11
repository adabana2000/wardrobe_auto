from app.core.celery_app import celery_app


@celery_app.task
def process_image_task(image_path: str):
    """
    画像処理タスク
    Phase 2で実装予定：YOLO, CLIP, rembgによる衣類認識
    """
    return {
        "status": "pending",
        "message": "Image processing to be implemented in Phase 2",
        "image_path": image_path
    }


@celery_app.task
def generate_outfit_task(weather_data: dict, schedule_data: dict):
    """
    コーディネート生成タスク
    Phase 2で実装予定：LLMによるコーディネート提案
    """
    return {
        "status": "pending",
        "message": "Outfit generation to be implemented in Phase 2"
    }
