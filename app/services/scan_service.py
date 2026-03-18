#
# scan_service.py
# FoodMind Backend
#
# app/services/scan_service.py
#

import base64
from app.services.gemini_service import analyse_food, validate_results
from app.db.database import SessionLocal
from app.db.models_scan import ScanDB

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

        image_bytes   = base64.b64decode(image_base64)
        gemini_result = await analyse_food(
            image_bytes=image_bytes,
            mobilenet_hint=mobilenet_hint,
            mobilenet_confidence=mobilenet_confidence
        )
        validation = validate_results(
            mobilenet_dish=mobilenet_hint,
            mobilenet_confidence=mobilenet_confidence,
            gemini_result=gemini_result
        )

        # ← Save to DB
        await self.save_scan(
            user_id=user_id,
            gemini_result=gemini_result,
            validation=validation,
            mobilenet_hint=mobilenet_hint,
            mobilenet_confidence=mobilenet_confidence
        )

        return {
            "type":       "scan_result",
            "result":     gemini_result.to_dict(),
            "validation": validation
        }

    async def save_scan(
        self,
        user_id: str,
        gemini_result,
        validation: dict,
        mobilenet_hint: str,
        mobilenet_confidence: float
    ):
        try:
            db = SessionLocal()
            scan = ScanDB(
                user_id              = user_id,
                dish_name            = gemini_result.dish_name,
                cuisine              = gemini_result.cuisine,
                calories             = gemini_result.calories,
                protein_g            = gemini_result.protein_g,
                carbs_g              = gemini_result.carbs_g,
                fat_g                = gemini_result.fat_g,
                fiber_g              = gemini_result.fiber_g,
                health_score         = gemini_result.health_score,
                confidence           = gemini_result.confidence,
                validation_level     = validation["validation_level"],
                final_confidence     = validation["final_confidence"],
                mobilenet_dish       = mobilenet_hint,
                mobilenet_confidence = mobilenet_confidence,
                gemini_dish          = gemini_result.dish_name,
                ingredients          = gemini_result.ingredients,
                recipe_steps         = gemini_result.recipe_steps,
                tags                 = gemini_result.tags,
                allergens            = gemini_result.allergens,
                cooking_tip          = gemini_result.cooking_tip,
                portion_size         = gemini_result.portion_size
            )
            db.add(scan)
            db.commit()
            print(f"Scan saved: {gemini_result.dish_name}")
        except Exception as e:
            print(f"Save error: {e}")
        finally:
            db.close()


# Singleton instance
# Import this in websocket.py
scan_service = ScanService()