#
# scan_service.py
# FoodMind Backend
#
# app/services/scan_service.py
#

import base64
from app.services.gemini_service import analyse_food, validate_results


class ScanService:

    # ─────────────────────────────────
    # MARK: — Process Scan
    # Main orchestrator
    # Called by websocket.py
    # ─────────────────────────────────
    async def process_scan(
        self,
        image_base64: str,
        mobilenet_hint: str,
        mobilenet_confidence: float,
        user_id: str
    ) -> dict:
        """
        Full scan pipeline:
        1. Decode base64 image
        2. Send to Gemini Flash
        3. Validate results
        4. Return formatted result
        """

        try:
            # ── Step 1: Decode image ───────
            image_bytes = base64.b64decode(image_base64)

            print(f"Processing scan for user: {user_id}")
            print(f"MobileNet hint: {mobilenet_hint} "
                  f"({int(mobilenet_confidence * 100)}%)")

            # ── Step 2: Gemini analysis ────
            gemini_result = await analyse_food(
                image_bytes=image_bytes,
                mobilenet_hint=mobilenet_hint,
                mobilenet_confidence=mobilenet_confidence
            )

            # ── Step 3: Validate ───────────
            validation = validate_results(
                mobilenet_dish=mobilenet_hint,
                mobilenet_confidence=mobilenet_confidence,
                gemini_result=gemini_result
            )

            print(f"Result: {gemini_result.dish_name} "
                  f"({gemini_result.calories} kcal) "
                  f"validation: {validation['validation_level']}")

            # ── Step 4: Return ─────────────
            return {
                "type":       "scan_result",
                "result":     gemini_result.to_dict(),
                "validation": validation
            }

        except Exception as e:
            print(f"Scan error: {e}")
            return {
                "type":    "scan_error",
                "message": str(e)
            }


# Singleton instance
# Import this in websocket.py
scan_service = ScanService()