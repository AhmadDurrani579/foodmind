#
# segformer_service.py
# FoodMind Backend
#

import io
import numpy as np
from PIL import Image

# ── Lazy globals ──────────────────────
processor = None
model     = None

MODEL_NAME = "LightDestory/segformer-b0-finetuned-segments-food-oct-24v2"

def load_model():
    global processor, model
    if model is not None:
        return True  # already loaded

    try:
        # ← Import inside function not at top
        import torch
        from transformers import (
            SegformerImageProcessor,
            SegformerForSemanticSegmentation
        )

        print("⏳ Loading SegFormer food model...")
        processor = SegformerImageProcessor.from_pretrained(MODEL_NAME)
        model     = SegformerForSemanticSegmentation.from_pretrained(
            MODEL_NAME
        )
        model.eval()
        print("✅ SegFormer loaded successfully")
        return True

    except Exception as e:
        print(f"❌ SegFormer load failed: {e}")
        model = None
        return False


async def segment_food(image_bytes: bytes) -> list[dict]:
    try:
        # ← Import torch here too
        import torch

        if not load_model():
            return []

        image  = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        orig_w, orig_h = image.size

        inputs = processor(images=image, return_tensors="pt")

        with torch.no_grad():
            outputs = model(**inputs)

        logits = outputs.logits

        upsampled = torch.nn.functional.interpolate(
            logits,
            size=(orig_h, orig_w),
            mode="bilinear",
            align_corners=False
        )

        seg_map = upsampled.argmax(dim=1).squeeze().numpy()

        id2label    = model.config.id2label
        total_px    = orig_w * orig_h
        segments    = []
        seen_labels = set()

        for label_id, label_name in id2label.items():
            if label_name.lower() in ["background", "other", "misc"]:
                continue

            mask        = (seg_map == label_id)
            pixel_count = mask.sum()
            area        = pixel_count / total_px

            if area < 0.02:
                continue

            if label_name in seen_labels:
                continue
            seen_labels.add(label_name)

            rows = np.any(mask, axis=1)
            cols = np.any(mask, axis=0)
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]

            bbox = [
                round(float(cmin / orig_w), 3),
                round(float(rmin / orig_h), 3),
                round(float((cmax - cmin) / orig_w), 3),
                round(float((rmax - rmin) / orig_h), 3)
            ]

            segments.append({
                "label":    label_name,
                "area":     round(float(area), 3),
                "bbox":     bbox,
                "label_id": int(label_id)
            })

        segments.sort(key=lambda x: x["area"], reverse=True)
        result = segments[:8]

        print(f"✅ SegFormer found {len(result)} ingredients: "
              f"{[s['label'] for s in result]}")

        return result

    except Exception as e:
        print(f"❌ SegFormer error: {e}")
        return []


def segments_to_description(segments: list[dict]) -> str:
    if not segments:
        return ""
    parts = []
    for seg in segments:
        pct = int(seg["area"] * 100)
        parts.append(f"{seg['label']} ({pct}% of image)")
    return "Visible ingredients detected: " + ", ".join(parts)