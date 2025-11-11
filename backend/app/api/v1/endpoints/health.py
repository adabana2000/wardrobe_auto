from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
import redis
from app.core.config import settings

router = APIRouter()


@router.get("")
async def health_check(db: Session = Depends(get_db)):
    """
    ヘルスチェックエンドポイント
    データベースとRedisの接続状態を確認
    """
    health_status = {
        "status": "healthy",
        "database": "disconnected",
        "redis": "disconnected"
    }

    # Check database connection
    try:
        db.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database_error"] = str(e)

    # Check Redis connection
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["redis_error"] = str(e)

    return health_status
