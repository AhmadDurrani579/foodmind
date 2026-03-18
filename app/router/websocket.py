#
# websocket.py
# FoodMind Backend
#
# app/routers/websocket.py
#

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from app.core.config import settings

router = APIRouter()

# ─────────────────────────────────────
# MARK: — JWT Verify
# ─────────────────────────────────────
def verify_jwt(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# ─────────────────────────────────────
# MARK: — WebSocket Endpoint
# ws://localhost:8000/ws/scan?token=JWT
# ─────────────────────────────────────
@router.websocket("/ws/scan")
async def scan_socket(websocket: WebSocket):

    # ── Step 1: Get token from query ──
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    token = token.strip()

    # ── Step 2: Verify token ──────────
    user = verify_jwt(token)

    if not user:
        await websocket.close(code=1008)
        return

    # ── Step 3: Accept connection ─────
    await websocket.accept()
    user_id = user.get("id")
    print(f"WebSocket connected — user: {user_id}")

    # ── Step 4: Send welcome ──────────
    await websocket.send_json({
        "type":    "connected",
        "message": "WebSocket connected successfully",
        "user_id": str(user_id)
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            # ── Ping ──────────────────
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            # ── Scan ──────────────────
            elif msg_type == "scan":
                from app.services.scan_service import scan_service

                await websocket.send_json({
                    "type":    "scan_started",
                    "message": "Analysing your food..."
                })

                result = await scan_service.process_scan(
                    image_base64=data.get("image", ""),
                    mobilenet_hint=data.get("mobilenet", {}).get("dish", "unknown"),
                    mobilenet_confidence=data.get("mobilenet", {}).get("confidence", 0.0),
                    user_id=str(user_id)
                )

                await websocket.send_json(result)

            # ── Unknown ───────────────
            else:
                await websocket.send_json({
                    "type":    "error",
                    "message": f"Unknown type: {msg_type}"
                })

    except WebSocketDisconnect:
        print(f"📱 Disconnected — user: {user_id}")

    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.send_json({
                "type":    "error",
                "message": str(e)
            })
        except:
            pass