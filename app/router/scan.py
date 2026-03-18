# app/routers/scan.py
#
# HTTP scan endpoints
# For testing without WebSocket
#

from fastapi import APIRouter, UploadFile, File
from app.services.scan_service import scan_service
import base64

router = APIRouter(prefix="/scan", tags=["scan"])

@router.post("/test")
async def test_scan(
    file: UploadFile = File(...),
    mobilenet_hint: str = "unknown",
    mobilenet_confidence: float = 0.0
):
    """Test endpoint — upload image via HTTP"""
    image_bytes  = await file.read()
    image_base64 = base64.b64encode(image_bytes).decode()

    result = await scan_service.process_scan(
        image_base64=image_base64,
        mobilenet_hint=mobilenet_hint,
        mobilenet_confidence=mobilenet_confidence,
        user_id="test_user"
    )
    return result