#
# sketchfab_service.py
# FoodMind Backend
#
# app/services/sketchfab_service.py
#

import httpx
import asyncio
from app.core.config import settings

# ─────────────────────────────────────
# MARK: — Constants
# ─────────────────────────────────────
SKETCHFAB_API  = "https://api.sketchfab.com/v3"
SKETCHFAB_TOKEN = settings.SKETCHFAB_TOKEN

# ─────────────────────────────────────
# MARK: — Dish → Search Query Map
# Maps Gemini dish names to better
# Sketchfab search terms
# ─────────────────────────────────────
DISH_SEARCH_MAP = {
    "pizza":      "pizza food realistic",
    "burger":     "burger hamburger realistic",
    "sushi":      "sushi japanese food",
    "sandwich":   "sandwich food realistic",
    "salad":      "salad bowl food",
    "pasta":      "pasta spaghetti food",
    "cake":       "cake dessert realistic",
    "donut":      "donut doughnut food",
    "waffle":     "waffle food realistic",
    "chicken":    "grilled chicken food",
    "steak":      "steak meat food",
    "taco":       "taco mexican food",
    "hotdog":     "hot dog food",
    "ice cream":  "ice cream dessert",
    "soup":       "soup bowl food",
    "noodles":    "noodles ramen food",
    "rice":       "rice bowl food",
    "fish":       "fish food realistic",
    "shrimp":     "shrimp seafood",
    "bread":      "bread loaf food",
}

def get_search_query(dish_name: str) -> str:
    """
    Maps dish name to best Sketchfab search query
    """
    dish_lower = dish_name.lower()

    # Check exact mappings first
    for key, query in DISH_SEARCH_MAP.items():
        if key in dish_lower:
            return query

    # Fallback — use dish name directly
    # Take first 2 words for better results
    words = dish_name.split()[:2]
    return " ".join(words) + " food 3d"


# ─────────────────────────────────────
# MARK: — Search Models
# ─────────────────────────────────────
async def search_food_model(dish_name: str) -> dict | None:
    """
    Searches Sketchfab for a food model
    matching the dish name.

    Returns model info or None if not found.
    """
    query = get_search_query(dish_name)
    print(f"🔍 Sketchfab search: '{query}' for dish '{dish_name}'")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{SKETCHFAB_API}/models",
                params={
                    "q":            query,
                    "downloadable": "true",
                    "license":      "by",        # CC Attribution
                    "count":        5,
                    "sort_by":      "-likeCount", # most liked first
                    "type":         "models",
                },
                headers={
                    "Authorization": f"Token {SKETCHFAB_TOKEN}"
                }
            )

            if response.status_code != 200:
                print(f"Sketchfab search failed: {response.status_code}")
                return None

            data     = response.json()
            results  = data.get("results", [])

            if not results:
                print(f"⚠️ No models found for '{query}'")
                return None

            # Pick best model (first result = most liked)
            model = results[0]
            print(f"✅ Found model: {model['name']} (uid: {model['uid']})")

            return {
                "uid":       model["uid"],
                "name":      model["name"],
                "author":    model.get("user", {}).get("username", "unknown"),
                "license":   model.get("license", {}).get("label", "CC Attribution"),
                "thumbnail": _get_thumbnail(model),
            }

    except Exception as e:
        print(f"Sketchfab search error: {e}")
        return None


# ─────────────────────────────────────
# MARK: — Get Download URL
# ─────────────────────────────────────
async def get_model_download_url(uid: str) -> dict | None:
    """
    Gets temporary download URLs for a model.
    Returns USDZ URL (preferred) or GLB URL.
    URLs expire after 300 seconds.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{SKETCHFAB_API}/models/{uid}/download",
                headers={
                    "Authorization": f"Token {SKETCHFAB_TOKEN}"
                }
            )

            if response.status_code == 403:
                print(f"Model {uid} not downloadable (403)")
                return None

            if response.status_code != 200:
                print(f"Download failed: {response.status_code}")
                return None

            data = response.json()

            # Prefer USDZ for iOS ARKit
            if "usdz" in data:
                url = data["usdz"]["url"]
                print(f"✅ Got USDZ URL for {uid}")
                return {
                    "url":    url,
                    "format": "usdz"
                }

            # Fallback to GLB
            if "gltf" in data:
                url = data["gltf"]["url"]
                print(f"✅ Got GLB URL for {uid}")
                return {
                    "url":    url,
                    "format": "glb"
                }

            print(f"⚠️ No download URL found for {uid}")
            return None

    except Exception as e:
        print(f" Download URL error: {e}")
        return None


# ─────────────────────────────────────
# MARK: — Main Function
# Search + Get Download URL in one call
# ─────────────────────────────────────
async def get_3d_model_for_dish(dish_name: str) -> dict | None:
    """
    Complete flow:
    1. Search Sketchfab for food model
    2. Get temporary download URL
    3. Download model bytes
    4. Upload to Cloudinary (permanent)
    5. Return permanent URL + model info
 
    Returns:
    {
        "url":     "https://cloudinary.com/...",
        "format":  "usdz" or "glb",
        "name":    "Pizza Model",
        "author":  "sketchfab_user",
        "license": "CC Attribution"
    }
    """
    if not SKETCHFAB_TOKEN:
        print("⚠️ No Sketchfab token configured")
        return None
 
    query = get_search_query(dish_name)
    print(f"🔍 Sketchfab search: '{query}' for '{dish_name}'")
 
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
 
            # ── Step 1: Search models ─────────
            response = await client.get(
                f"{SKETCHFAB_API}/models",
                params={
                    "q":            query,
                    "downloadable": "true",
                    "license":      "by",
                    "count":        10,
                    "sort_by":      "-likeCount",
                    "categories":   "food-drink",
                },
                headers={
                    "Authorization": f"Token {SKETCHFAB_TOKEN}"
                }
            )
 
            if response.status_code != 200:
                print(f"❌ Sketchfab search failed: {response.status_code}")
                return None
 
            results = response.json().get("results", [])

            NON_FOOD_KEYWORDS = [
                "girl", "boy", "character", "human", "person",
                "robot", "car", "building", "weapon", "gun",
                "scifi", "sci-fi", "anime", "vehicle", "sword"
            ]
            results = [
                r for r in results
                if not any(
                    kw in r["name"].lower()
                    for kw in NON_FOOD_KEYWORDS
                )
            ]

            if not results:
                print(f"⚠️ No models found for '{query}'")
                return None
 
            # ── Step 2: Find downloadable model ──
            for candidate in results:
                uid  = candidate["uid"]
                name = candidate["name"]
 
                # Get temp download URL
                download = await get_model_download_url(uid)
                if not download:
                    await asyncio.sleep(0.3)
                    continue
 
                temp_url = download["url"]
                fmt      = download["format"]
 
                print(f"⬇️ Downloading {fmt} model: {name}...")
 
                # ── Step 3: Download model bytes ──
                try:
                    model_response = await client.get(
                        temp_url,
                        timeout=30.0,
                        follow_redirects=True
                    )
 
                    if model_response.status_code != 200:
                        print(f" Model download failed: {model_response.status_code}")
                        await asyncio.sleep(0.3)
                        continue
 
                    model_bytes = model_response.content
                    size_mb     = len(model_bytes) / (1024 * 1024)
                    print(f"✅ Downloaded {size_mb:.1f}MB {fmt} model")
 
                    # Skip models over 30MB (too slow for mobile)
                    if size_mb > 8:
                        print(f" Model too large ({size_mb:.1f}MB) → skipping")
                        await asyncio.sleep(0.3)
                        continue
 
                except Exception as e:
                    print(f" Download error: {e}")
                    await asyncio.sleep(0.3)
                    continue
 
                # ── Step 4: Upload to Cloudinary ──
                permanent_url = await _upload_model_to_cloudinary(
                    model_bytes=model_bytes,
                    dish_name=dish_name,
                    fmt=fmt
                )
 
                if not permanent_url:
                    print("⚠️ Cloudinary upload failed → using temp URL")
                    permanent_url = temp_url  # fallback to temp
 
                print(f"🎯 3D model ready: {name} → {permanent_url[:60]}...")
 
                return {
                    "url":     permanent_url,
                    "format":  fmt,
                    "name":    name,
                    "author":  candidate.get("user", {}).get("username", "unknown"),
                    "license": candidate.get("license", {}).get("label", "CC Attribution"),
                    "uid":     uid
                }
 
    except Exception as e:
        print(f" get_3d_model_for_dish error: {e}")
 
    return None

# ─────────────────────────────────────
# MARK: — Upload Model To Cloudinary
# ─────────────────────────────────────
async def _upload_model_to_cloudinary(
    model_bytes: bytes,
    dish_name:   str,
    fmt:         str
) -> str | None:
    """
    Uploads 3D model to Cloudinary for permanent storage.
    Returns permanent URL or None if failed.
    """
    try:
        import cloudinary
        import cloudinary.uploader
        import re
 
        # Clean dish name for public_id
        clean = re.sub(r'[^a-z0-9]', '_', dish_name.lower())
        clean = re.sub(r'_+', '_', clean).strip('_')[:40]
 
        public_id = f"foodmind/models/{clean}"
 
        print(f"Uploading model to Cloudinary: {public_id}")
 
        result = cloudinary.uploader.upload(
            model_bytes,
            public_id=public_id,
            resource_type="raw",        # ← raw for 3D files
            format=fmt,
            overwrite=True,             # ← cache — reuse same model
        )
 
        url = result.get("secure_url", "")
        if url:
            print(f"✅ Cloudinary upload success: {url[:60]}...")
            return url
 
    except Exception as e:
        print(f" Cloudinary 3D upload error: {e}")
 
    return None


# ─────────────────────────────────────
# MARK: — Helpers
# ─────────────────────────────────────
def _get_thumbnail(model: dict) -> str:
    """Gets best thumbnail URL from model"""
    try:
        thumbnails = model.get("thumbnails", {}).get("images", [])
        if thumbnails:
            # Get largest thumbnail
            sorted_t = sorted(
                thumbnails,
                key=lambda x: x.get("width", 0),
                reverse=True
            )
            return sorted_t[0].get("url", "")
    except Exception:
        pass
    return ""