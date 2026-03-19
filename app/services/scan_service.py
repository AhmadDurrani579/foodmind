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
from app.services.cloudinary_service import upload_image
from app.services.segformer_service import segment_food, segments_to_description

# ─────────────────────────────────────
# MARK: — Segment Validator
# Standalone function (not a method)
# ─────────────────────────────────────
def validate_segments(
    segments: list,
    mobilenet_hint: str
) -> list:
    """
    Cross-validates SegFormer segments
    against CoreML dish prediction.
    Removes segments that don't make
    sense for the detected dish.
    """
    if not segments:
        return []

    DISH_INGREDIENTS = {
        "pizza":      ["cheese", "tomato", "dough", "pepper", "mushroom", "meat"],
        "burger":     ["bun", "meat", "lettuce", "tomato", "cheese", "onion"],
        "salad":      ["lettuce", "tomato", "cucumber", "carrot", "onion"],
        "sushi":      ["rice", "fish", "seaweed", "salmon", "tuna", "avocado"],
        "sandwich":   ["bread", "meat", "lettuce", "tomato", "cheese"],
        "pasta":      ["pasta", "tomato", "meat", "cheese", "mushroom"],
        "soup":       ["broth", "vegetable", "meat", "carrot", "onion"],
        "waffle":     ["waffle", "syrup", "butter", "cream", "berry"],
        "pancake":    ["pancake", "syrup", "butter", "cream", "berry"],
        "cake":       ["cake", "cream", "chocolate", "berry", "sugar"],
        "ice_cream":  ["cream", "chocolate", "berry", "cone", "vanilla"],
        "samosa":     ["potato", "pastry", "pea", "spice"],
        "hot_dog":    ["sausage", "bun", "mustard", "ketchup"],
        "steak":      ["meat", "potato", "vegetable", "sauce"],
        "chicken":    ["chicken", "vegetable", "sauce", "potato"],
        "chocolate":  ["chocolate", "cream", "cake", "cocoa"],
        "donut":      ["dough", "cream", "chocolate", "sugar"],
        "apple_pie":  ["apple", "pastry", "sugar", "cream"],
        "omelette":   ["egg", "cheese", "vegetable", "meat"],
        "fish":       ["fish", "sauce", "vegetable", "lemon"],
        "shrimp":     ["shrimp", "sauce", "vegetable", "rice"],
    }

    hint_lower = mobilenet_hint.lower().replace("_", " ")
    matching_ingredients = []

    for dish, ingredients in DISH_INGREDIENTS.items():
        if dish in hint_lower or hint_lower in dish:
            matching_ingredients = ingredients
            break

    # No match → return segments as is, let Gemini decide
    if not matching_ingredients:
        print(f"⚠️ No ingredient mapping for '{mobilenet_hint}' "
              f"→ using raw segments")
        return segments

    # Filter segments matching expected ingredients
    validated = [
        seg for seg in segments
        if any(
            ing in seg["label"].lower()
            for ing in matching_ingredients
        )
    ]

    if not validated:
        print(f"⚠️ No valid segments for '{mobilenet_hint}' "
              f"→ skipping segments")
        return []

    print(f"✅ Validated {len(validated)}/{len(segments)} segments "
          f"for '{mobilenet_hint}'")
    return validated


# ─────────────────────────────────────
# MARK: — ScanService
# ─────────────────────────────────────
class ScanService:

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

            # ── Step 1: SegFormer ─────────
            segments = await segment_food(image_bytes)

            # ── Step 2: Validate segments ──
            validated_segments = validate_segments(
                segments=segments,
                mobilenet_hint=mobilenet_hint
            )
            segment_description = segments_to_description(
                validated_segments
            )
            print(f"🔬 Segments: {segment_description}")

            # ── Step 3: Gemini ────────────
            gemini_result = await analyse_food(
                image_bytes=image_bytes,
                mobilenet_hint=mobilenet_hint,
                mobilenet_confidence=mobilenet_confidence,
                segment_description=segment_description
            )

            # ── Step 4: Validate results ──
            validation = validate_results(
                mobilenet_dish=mobilenet_hint,
                mobilenet_confidence=mobilenet_confidence,
                gemini_result=gemini_result
            )

            # ── Step 5: Upload image ──────
            image_url = ""
            try:
                image_url = await upload_image(
                    image_bytes=image_bytes,
                    user_id=user_id,
                    dish_name=gemini_result.dish_name
                )
            except Exception as e:
                print(f"⚠️ Cloudinary failed: {e}")

            # ── Step 6: Save to DB ────────
            await self.save_scan(
                user_id=user_id,
                gemini_result=gemini_result,
                validation=validation,
                mobilenet_hint=mobilenet_hint,
                mobilenet_confidence=mobilenet_confidence,
                image_url=image_url
            )

            print(f"📦 Returning {len(validated_segments)} segments")

            # ── Step 7: Return ────────────
            return {
                "type":       "scan_result",
                "result":     gemini_result.to_dict(),
                "validation": validation,
                "segments":   validated_segments,
                "image_url":  image_url
            }

        except Exception as e:
            print(f"❌ Scan error: {e}")
            return {
                "type":    "scan_error",
                "message": str(e)
            }

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