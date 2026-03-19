#
# gemini_service.py
# FoodMind Backend
#
# app/services/gemini_service.py
#

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
import itertools
from app.core.config import settings

load_dotenv()

API_KEYS = [k for k in [
    settings.GEMINI_API_KEY,
    settings.GEMINI_API_KEY_1,
    settings.GEMINI_API_KEY_2,
    settings.GEMINI_API_KEY_3,
    settings.GEMINI_API_KEY_4,
    settings.GEMINI_API_KEY_5,
] if k]  # filter empty keys

current_key_index = 0

# ─────────────────────────────────────
# MARK: — Gemini Client Setup
# ─────────────────────────────────────
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODELS = [
    "gemini-2.5-flash",        # primary
    "gemini-2.0-flash",        # fallback 1
]

def get_next_client():
    """Rotate to next API key"""
    global current_key_index
    if not API_KEYS:
        return None
    key = API_KEYS[current_key_index % len(API_KEYS)]
    current_key_index += 1
    return genai.Client(api_key=key)


# ─────────────────────────────────────
# MARK: — Prompt
# ─────────────────────────────────────
FOOD_ANALYSIS_PROMPT = """
You are a professional nutritionist and chef.
Analyse this food image carefully.

You have been given a hint from an on-device AI model
that this might be: {mobilenet_hint} (confidence: {mobilenet_confidence}%)

Use the image as your primary source.
The hint is just a suggestion — trust your own analysis.

IMPORTANT: For each ingredient, carefully look at the image
and identify WHERE in the image that ingredient appears.
Use these position values only:
top-left, top-center, top-right,
center-left, center, center-right,
bottom-left, bottom-center, bottom-right

Return ONLY a valid JSON object.
No markdown. No explanation. No extra text.
Just the raw JSON.

{{
  "dish_name": "exact dish name",
  "cuisine": "Italian/Asian/British/American/etc",
  "calories": 620,
  "protein_g": 28.5,
  "carbs_g": 74.0,
  "fat_g": 18.2,
  "fiber_g": 3.2,
  "confidence": 91,
  "health_score": 72,
  "portion_size": "Medium (approx 400g)",
  "ingredients": [
    {{
      "name": "Spaghetti pasta",
      "calories": 280,
      "grams": 200,
      "emoji": "🍝",
      "position": "center"
    }},
    {{
      "name": "Beef mince",
      "calories": 190,
      "grams": 150,
      "emoji": "🥩",
      "position": "top-center"
    }},
    {{
      "name": "Tomato sauce",
      "calories": 60,
      "grams": 100,
      "emoji": "🍅",
      "position": "center-left"
    }}
  ],
  "recipe_steps": [
    {{
      "step": 1,
      "title": "Boil pasta",
      "description": "Cook spaghetti in salted boiling water for 10 minutes until al dente.",
      "duration_mins": 10
    }},
    {{
      "step": 2,
      "title": "Brown the mince",
      "description": "Fry beef mince in olive oil over high heat until browned.",
      "duration_mins": 8
    }}
  ],
  "cooking_tip": "Add a splash of red wine when browning the mince for deeper flavour",
  "tags": ["High protein", "Italian", "Comfort food"],
  "allergens": ["Gluten", "Dairy"]
}}
"""
# ─────────────────────────────────────
# MARK: — Analysis Result Model
# ─────────────────────────────────────
class FoodAnalysisResult:
    def __init__(self, data: dict):
        self.dish_name    = data.get("dish_name", "Unknown dish")
        self.cuisine      = data.get("cuisine", "Unknown")
        self.calories     = data.get("calories", 0)
        self.protein_g    = data.get("protein_g", 0.0)
        self.carbs_g      = data.get("carbs_g", 0.0)
        self.fat_g        = data.get("fat_g", 0.0)
        self.fiber_g      = data.get("fiber_g", 0.0)
        self.confidence   = data.get("confidence", 0)
        self.health_score = data.get("health_score", 0)
        self.portion_size = data.get("portion_size", "")
        self.ingredients  = data.get("ingredients", [])
        self.recipe_steps = data.get("recipe_steps", [])
        self.cooking_tip  = data.get("cooking_tip", "")
        self.tags         = data.get("tags", [])
        self.allergens    = data.get("allergens", [])

    def to_dict(self) -> dict:
        return {
            "dish_name":    self.dish_name,
            "cuisine":      self.cuisine,
            "calories":     self.calories,
            "protein_g":    self.protein_g,
            "carbs_g":      self.carbs_g,
            "fat_g":        self.fat_g,
            "fiber_g":      self.fiber_g,
            "confidence":   self.confidence,
            "health_score": self.health_score,
            "portion_size": self.portion_size,
            "ingredients":  self.ingredients,
            "recipe_steps": self.recipe_steps,
            "cooking_tip":  self.cooking_tip,
            "tags":         self.tags,
            "allergens":    self.allergens,
            "image_url":      ""  # Placeholder for image URL
        }


# ─────────────────────────────────────
# MARK: — Main Analysis Function
# ─────────────────────────────────────
async def analyse_food(
    image_bytes: bytes,
    mobilenet_hint: str = "unknown",
    mobilenet_confidence: float = 0.0,
    segment_description: str = ""
) -> FoodAnalysisResult:

    import asyncio

    segment_context = (
        f"\n\nComputer vision ingredient hints "
        f"(use as supporting reference, "
        f"trust your visual analysis more): {segment_description}"
        if segment_description
        else ""
    )


    prompt = FOOD_ANALYSIS_PROMPT.format(
        mobilenet_hint=mobilenet_hint,
        mobilenet_confidence=int(mobilenet_confidence * 100)
    ) + segment_context

    # ── Try each model with each key ──
    for model_name in MODELS:
        for key_attempt in range(len(API_KEYS)):
            try:
                # Get rotated client
                api_client = get_next_client()
                if not api_client:
                    print("❌ No API keys configured")
                    return _fallback_result(mobilenet_hint)

                print(f"🤖 Trying {model_name} "
                      f"(key {(current_key_index-1) % len(API_KEYS) + 1}"
                      f"/{len(API_KEYS)})...")

                response = api_client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/jpeg"
                        ),
                        prompt
                    ]
                )

                raw_text = response.text.strip()

                if raw_text.startswith("```"):
                    raw_text = raw_text.split("```")[1]
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:]
                    raw_text = raw_text.strip()

                data   = json.loads(raw_text)
                result = FoodAnalysisResult(data)

                print(f"✅ {model_name}: {result.dish_name} "
                      f"({result.calories} kcal)")

                return result

            except json.JSONDecodeError as e:
                print(f"❌ JSON error: {e}")
                return _fallback_result(mobilenet_hint)

            except Exception as e:
                error_str = str(e)

                if "429" in error_str:
                    print(f"⚠️ {model_name} key "
                          f"{(current_key_index-1) % len(API_KEYS) + 1} "
                          f"rate limited → rotating key...")
                    continue  # try next key

                if "503" in error_str:
                    print(f"⚠️ {model_name} overloaded → trying next...")
                    await asyncio.sleep(3)
                    break

                print(f"❌ {model_name} error: {e}")
                break

    print("❌ All models + keys exhausted → fallback")
    return _fallback_result(mobilenet_hint)

# ─────────────────────────────────────
# MARK: — Validation Layer
# ─────────────────────────────────────
def validate_results(
    mobilenet_dish: str,
    mobilenet_confidence: float,
    gemini_result: FoodAnalysisResult,
    mobilenet_calories: int = 0
) -> dict:

    mobilenet_clean = mobilenet_dish.lower().replace("_", " ")
    gemini_clean    = gemini_result.dish_name.lower()

    dishes_agree = (
        mobilenet_clean in gemini_clean or
        gemini_clean in mobilenet_clean or
        _share_keywords(mobilenet_clean, gemini_clean)
    )

    if mobilenet_calories > 0:
        cal_diff     = abs(mobilenet_calories - gemini_result.calories)
        cal_diff_pct = cal_diff / max(mobilenet_calories, 1) * 100
    else:
        cal_diff_pct = 0

    if dishes_agree and cal_diff_pct < 20:
        validation       = "high"
        final_confidence = min(
            95,
            int((mobilenet_confidence * 100 + gemini_result.confidence) / 2)
        )
    elif dishes_agree:
        validation       = "medium"
        final_confidence = gemini_result.confidence
    else:
        validation       = "low"
        final_confidence = int(max(
            mobilenet_confidence * 100,
            gemini_result.confidence
        ))

    return {
        "validation_level": validation,
        "dishes_agree":     dishes_agree,
        "calorie_diff_pct": round(cal_diff_pct, 1),
        "final_confidence": int(final_confidence),
        "validated_by":     ["MobileNet", "Gemini 2.5 Flash"],
        "mobilenet_dish":   mobilenet_dish,
        "gemini_dish":      gemini_result.dish_name
    }


# ─────────────────────────────────────
# MARK: — Helpers
# ─────────────────────────────────────
def _share_keywords(dish1: str, dish2: str) -> bool:
    keywords1 = set(dish1.split())
    keywords2 = set(dish2.split())
    common    = keywords1.intersection(keywords2)
    ignore    = {"with", "and", "the", "a", "of", "in"}
    common   -= ignore
    return len(common) > 0


def _fallback_result(hint: str) -> FoodAnalysisResult:
    return FoodAnalysisResult({
        "dish_name":    hint.replace("_", " ").title()
                        if hint != "unknown" else "Unknown dish",
        "cuisine":      "Unknown",
        "calories":     0,
        "protein_g":    0,
        "carbs_g":      0,
        "fat_g":        0,
        "fiber_g":      0,
        "confidence":   0,
        "health_score": 0,
        "portion_size": "Unknown",
        "ingredients":  [],
        "recipe_steps": [],
        "cooking_tip":  "Could not analyse this image. Please try again.",
        "tags":         [],
        "allergens":    []
    })