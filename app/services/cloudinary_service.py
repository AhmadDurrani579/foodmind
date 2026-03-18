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
    """
    Upload image to Cloudinary
    Returns permanent URL
    """
    try:
        # Create folder per user
        folder = f"foodmind/{user_id}"

        # Clean dish name for public_id
        clean_name = dish_name.lower()\
            .replace(" ", "_")\
            .replace("/", "_")

        import time
        public_id = f"{folder}/{clean_name}_{int(time.time())}"

        # Upload
        result = cloudinary.uploader.upload(
            image_bytes,
            public_id    = public_id,
            folder       = folder,
            resource_type = "image",
            transformation = [
                {"width": 800, "crop": "limit"},  # max 800px
                {"quality": "auto"}               # auto compress
            ]
        )

        url = result.get("secure_url", "")
        print(f"✅ Image uploaded: {url}")
        return url

    except Exception as e:
        print(f"Cloudinary error: {e}")
        return ""