# app/services/cloudinary_service.py

import cloudinary
import cloudinary.uploader
import os
import time
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key    = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

async def upload_image(
    image_bytes: bytes,
    user_id:     str,
    dish_name:   str = "food"
) -> str:
  
    try:
        clean_name = dish_name.lower()\
            .replace(" ", "_")\
            .replace("/", "_")\
            .replace("(", "")\
            .replace(")", "")

        public_id = f"foodmind/{user_id}/{clean_name}_{int(time.time())}"

        # ← Remove folder= parameter
        # public_id already contains the full path
        result = cloudinary.uploader.upload(
            image_bytes,
            public_id     = public_id,
            resource_type = "image",
            transformation = [
                {"width": 800, "crop": "limit"},
                {"quality": "auto"}
            ]
        )

        return result.get("secure_url", "")

    except Exception as e:
        print(f"❌ Cloudinary error: {e}")
        return ""
