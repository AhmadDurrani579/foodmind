# app/routers/scan.py
#
# HTTP scan endpoints
# For testing without WebSocket
#

from fastapi import APIRouter, UploadFile, File
from app.services.scan_service import scan_service
import base64
from app.router import websocket, auth, users, scan

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
 
from app.db.database import get_db
from app.db.models_scan import ScanDB
from app.schemas.scan import ScanResponse
from app.core.dependencies import get_current_user
from app.models.user import User


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

@router.get("/me", response_model=List[ScanResponse])
def get_my_scans(
    limit:        int     = 20,
    offset:       int     = 0,
    current_user: User  = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    scans = db.query(ScanDB)\
        .filter(ScanDB.user_id == current_user.id)\
        .order_by(ScanDB.created_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()
 
    return scans

# ─────────────────────────────────────
# MARK: — Get Single Scan
# GET /scans/{scan_id}
# ─────────────────────────────────────
@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan(
    scan_id:      UUID,
    current_user: User  = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    scan = db.query(ScanDB)\
        .filter(
            ScanDB.id      == scan_id,
            ScanDB.user_id == current_user.id
        )\
        .first()
 
    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan not found"
        )
 
    return scan
 
# ─────────────────────────────────────
# MARK: — Get Scan Stats
# GET /scans/stats/me
# Returns weekly nutrition summary
# ─────────────────────────────────────
@router.get("/stats/me")
def get_my_stats(
    current_user: User  = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    from sqlalchemy import func
    from datetime import datetime, timedelta
 
    # Last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
 
    scans = db.query(ScanDB)\
        .filter(
            ScanDB.user_id   == current_user.id,
            ScanDB.created_at >= week_ago
        )\
        .all()
 
    if not scans:
        return {
            "total_scans":   0,
            "avg_calories":  0,
            "avg_protein":   0,
            "avg_carbs":     0,
            "avg_fat":       0,
            "total_this_week": 0
        }
 
    total        = len(scans)
    avg_calories = sum(s.calories or 0 for s in scans) // total
    avg_protein  = sum(s.protein_g or 0 for s in scans) / total
    avg_carbs    = sum(s.carbs_g or 0 for s in scans) / total
    avg_fat      = sum(s.fat_g or 0 for s in scans) / total
 
    return {
        "total_scans":     total,
        "avg_calories":    avg_calories,
        "avg_protein":     round(avg_protein, 1),
        "avg_carbs":       round(avg_carbs, 1),
        "avg_fat":         round(avg_fat, 1),
        "total_this_week": total
    }

# ─────────────────────────────────────
# MARK: — Delete Scan
# DELETE /scans/{scan_id}
# ─────────────────────────────────────
@router.delete("/{scan_id}")
def delete_scan(
    scan_id:      UUID,
    current_user: User  = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    scan = db.query(ScanDB)\
        .filter(
            ScanDB.id      == scan_id,
            ScanDB.user_id == current_user.id
        )\
        .first()
 
    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan not found"
        )
 
    db.delete(scan)
    db.commit()
 
    return {"message": "Scan deleted"}
