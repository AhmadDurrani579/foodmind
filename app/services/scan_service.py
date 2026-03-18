import base64
from app.services.gemini_service import (
    analyse_food,
    validate_results
)

class ScanService:

    async def process_scan(
        self,
        image_base64: str,
        mobilenet_hint: str,
        mobilenet_confidence: float,
        user_id: str
    ) -> dict:
        """
        Main scan pipeline:
        1. Decode image
        2. Call Gemini Flash
        3. Validate results
        4. Save to DB (later)
        5. Return full result
        """

        # Step 1 — Decode image
        image_bytes = base64.b64decode(image_base64)

        # Step 2 — Gemini Flash analysis
        gemini_result = await analyse_food(
            image_bytes=image_bytes,
            mobilenet_hint=mobilenet_hint,
            mobilenet_confidence=mobilenet_confidence
        )

        # Step 3 — Validate
        validation = validate_results(
            mobilenet_dish=mobilenet_hint,
            mobilenet_confidence=mobilenet_confidence,
            gemini_result=gemini_result
        )

        # Step 4 — TODO: Save to DB
        # await db.save_scan(user_id, gemini_result)

        # Step 5 — Return
        return {
            "type":       "scan_result",
            "result":     gemini_result.to_dict(),
            "validation": validation
        }

# Singleton instance
scan_service = ScanService()
