#
# scan_service.py
# FoodMind Backend
#
# app/services/scan_service.py
#

import asyncio
import base64
from app.services.gemini_service import analyse_food, validate_results
from app.db.database import SessionLocal
from app.db.models_scan import ScanDB
from app.services.cloudinary_service import upload_image
from app.services.yolo_service import detect_food, estimate_calories
from app.services.sketchfab_service import get_3d_model_for_dish

FOOD_LABELS = [
                "pizza", "burger", "hot dog", "sandwich",
                "cake", "donut", "apple", "banana", "orange",
                "broccoli", "carrot", "bowl", "food", "plate",
                "sushi", "pasta", "salad", "chicken", "steak",
                "waffle", "pancake", "soup", "rice", "bread",
                "fish", "shrimp", "taco", "burrito", "noodles",
                "curry", "ice cream", "fries", "kebab", "dumpling"
        ]


class ScanService:


    # ─────────────────────────────────
    # MARK: — Process Scan
    # ─────────────────────────────────
    async def process_scan(
        self,
        image_base64: str,
        mobilenet_hint: str,
        mobilenet_confidence: float,
        user_id: str
    ) -> dict:

        try:
            if not image_base64:
                return {
                    "type":    "scan_error",
                    "message": "No image received"
                }

            image_bytes = base64.b64decode(image_base64)
            print(f"📸 Image: {len(image_bytes)} bytes")

            # ── Step 1: YOLO + Gemini parallel ──
            print("🔀 Running YOLO + Gemini in parallel...")

            yolo_task = asyncio.create_task(
                detect_food(image_bytes)
            )
            gemini_task = asyncio.create_task(
                analyse_food(
                    image_bytes=image_bytes,
                    mobilenet_hint=mobilenet_hint,
                    mobilenet_confidence=mobilenet_confidence
                )
            )

            yolo_result, gemini_result = await asyncio.gather(
                yolo_task,
                gemini_task,
                return_exceptions=True
            )

            # ── Step 2: Handle YOLO ──────────
            yolo_data = {}
            if isinstance(yolo_result, Exception):
                print(f"⚠️ YOLO failed: {yolo_result}")
                yolo_data = {
                    "detected":   False,
                    "label":      "unknown",
                    "confidence": 0.0,
                    "bbox_norm":  []
                }
            else:
                yolo_data = yolo_result
                if yolo_data.get("detected"):
                    print(f"🎯 YOLO: {yolo_data['label']} "
                          f"({int(yolo_data['confidence'] * 100)}%)")

            # ── Step 3: Handle Gemini ────────
            used_fallback = False
            if isinstance(gemini_result, Exception):
                print(f"Gemini failed → YOLO fallback")
                gemini_result = self._yolo_fallback(
                    yolo_data=yolo_data,
                    mobilenet_hint=mobilenet_hint
                )
                used_fallback = True

            # ── Step 4: Fusion confidence ────
            if (not used_fallback and
                yolo_data.get("detected") and
                yolo_data.get("confidence", 0) > 0 and
                any(food in yolo_data.get("label", "").lower()
                    for food in FOOD_LABELS)):

                yolo_conf        = int(yolo_data["confidence"] * 100)
                final_confidence = (gemini_result.confidence + yolo_conf) // 2
                print(f"🔀 Fusion: Gemini {gemini_result.confidence}% "
                      f"+ YOLO {yolo_conf}% = {final_confidence}%")
            else:
                final_confidence = gemini_result.confidence
                print(f"ℹ️ YOLO non-food detection → using Gemini confidence only")

            # ── Step 5: Validate ─────────────
            validation = validate_results(
                mobilenet_dish=mobilenet_hint,
                mobilenet_confidence=mobilenet_confidence,
                gemini_result=gemini_result
            )

            # ── Step 6: Upload image ─────────
            image_url = ""
            try:
                image_url = await upload_image(
                    image_bytes=image_bytes,
                    user_id=user_id,
                    dish_name=gemini_result.dish_name
                )
            except Exception as e:
                print(f"⚠️ Cloudinary failed: {e}")

            # ── Step 7: Get 3D Model ─────────  ← NEW
            model_3d = None
            try:
                model_3d = await asyncio.wait_for(
                    get_3d_model_for_dish(gemini_result.dish_name),
                    timeout=15.0  # ← max 15 seconds
                )
                if model_3d:
                    print(f"🎯 3D model: {model_3d['name']}")
            except asyncio.TimeoutError:
                print("⚠️ 3D model timeout → skipping")
            except Exception as e:
                print(f"⚠️ 3D model failed: {e}")

            # ── Step 8: Save to DB ───────────
            await self.save_scan(
                user_id=user_id,
                gemini_result=gemini_result,
                validation=validation,
                mobilenet_hint=mobilenet_hint,
                mobilenet_confidence=mobilenet_confidence,
                image_url=image_url
            )

            # ── Step 9: Return ───────────────
            result_dict = gemini_result.to_dict()
            result_dict["confidence"] = final_confidence

            return {
                "type":          "scan_result",
                "result":        result_dict,
                "validation":    validation,
                "yolo":          {
                    "detected":   yolo_data.get("detected", False),
                    "label":      yolo_data.get("label", ""),
                    "confidence": yolo_data.get("confidence", 0.0),
                    "bbox_norm":  yolo_data.get("bbox_norm", []),
                },
                "image_url":     image_url,
                "model_3d":      model_3d,       # ← NEW
                "used_fallback": used_fallback
            }

        except Exception as e:
            print(f"❌ Scan error: {e}")
            return {
                "type":    "scan_error",
                "message": str(e)
            }
     
    # ─────────────────────────────────
    # MARK: — YOLO Fallback
    # ─────────────────────────────────
    def _yolo_fallback(self, yolo_data: dict, mobilenet_hint: str):
        from app.services.gemini_service import _fallback_result
        label     = yolo_data.get("label", mobilenet_hint)
        result    = _fallback_result(label)
        estimated = estimate_calories(label)
        if estimated > 0:
            result.calories = estimated
        return result

    # ─────────────────────────────────
    # MARK: — Save Scan
    # ─────────────────────────────────
    async def save_scan(
        self,
        user_id: str,
        gemini_result,
        validation: dict,
        mobilenet_hint: str,
        mobilenet_confidence: float,
        image_url: str = ""
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
                image_url            = image_url
            )
            db.add(scan)
            db.commit()
            print(f"✅ Scan saved: {gemini_result.dish_name}")
        except Exception as e:
            print(f"❌ Save error: {e}")
            db.rollback()
        finally:
            db.close()


scan_service = ScanService()