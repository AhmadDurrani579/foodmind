#
# scan_service.py
# FoodMind Backend
#

import base64
from app.services.gemini_service import analyse_food, validate_results
from app.db.database import SessionLocal
from app.db.models_scan import ScanDB
from app.services.cloudinary_service import upload_image 
from app.services.segformer_service import segment_food, segments_to_description

class ScanService:

    # ─────────────────────────────────
    # MARK: — Process Scan
    # Main orchestrator
    # Called by websocket.py
    # ─────────────────────────────────
    async def process_scan(self, image_base64, mobilenet_hint, mobilenet_confidence, user_id):
        try:
            image_bytes = base64.b64decode(image_base64)
            print(f"📸 Image: {len(image_bytes)} bytes")

            # ── Step 1: SegFormer ─────────
            segments = await segment_food(image_bytes)
            segment_description = segments_to_description(segments)
            print(f"🔬 Segments: {segment_description}")

            # ── Step 2: Gemini (enhanced) ─
            gemini_result = await analyse_food(
                image_bytes=image_bytes,
                mobilenet_hint=mobilenet_hint,
                mobilenet_confidence=mobilenet_confidence,
                segment_description=segment_description  # ← pass to Gemini
            )

            # ── Step 3: Validate ──────────
            validation = validate_results(
                mobilenet_dish=mobilenet_hint,
                mobilenet_confidence=mobilenet_confidence,
                gemini_result=gemini_result
            )

            # ── Step 4: Upload image ──────
            image_url = ""
            try:
                image_url = await upload_image(
                    image_bytes=image_bytes,
                    user_id=user_id,
                    dish_name=gemini_result.dish_name
                )
            except Exception as e:
                print(f"⚠️ Cloudinary failed: {e}")

            # ── Step 5: Save to DB ────────
            await self.save_scan(
                user_id=user_id,
                gemini_result=gemini_result,
                validation=validation,
                mobilenet_hint=mobilenet_hint,
                mobilenet_confidence=mobilenet_confidence,
                image_url=image_url
            )
            print(f"📦 Returning segments: {segments}")

            # ── Step 6: Return ────────────
            return {
                "type":       "scan_result",
                "result":     gemini_result.to_dict(),
                "validation": validation,
                "segments":   segments,   # ← for ARKit later
                "image_url":  image_url
            }

        except Exception as e:
            print(f"❌ Scan error: {e}")
            return {"type": "scan_error", "message": str(e)}
    
    async def save_scan(
        self,
        user_id: str,
        gemini_result,
        validation: dict,
        mobilenet_hint: str,
        mobilenet_confidence: float,
        image_url: str = ""  # ← ADD HERE
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
                portion_size         = gemini_result.portion_size,
                image_url            = image_url  # ← ADD HERE
            )
            db.add(scan)
            db.commit()
            print(f" Scan saved: {gemini_result.dish_name}")
        except Exception as e:
            print(f" Save error: {e}")
            db.rollback()
        finally:
            db.close()

# Singleton instance
# Import this in websocket.py
scan_service = ScanService()