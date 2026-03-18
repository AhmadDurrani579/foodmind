from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.auth.jwt_handler import verify_token     

router =  APIRouter()

@router.websocket("/ws/scan")
async def scan_socket(websocket: WebSocket):

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    user = verify_token(token.strip())

    if not user:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    user_id = user.get("id")
    print(f"WebSocket connected — user: {user_id}")

    await websocket.send_json({
        "type":    "connected",
        "message": "WebSocket connected successfully",
        "user_id": str(user_id)
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

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

            else:
                await websocket.send_json({
                    "type":    "error",
                    "message": f"Unknown type: {msg_type}"
                })

    except WebSocketDisconnect:
        print(f"Disconnected — user: {user_id}")
    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass