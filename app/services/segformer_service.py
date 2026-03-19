#
# segformer_service.py
# FoodMind Backend
#

import io
import torch
import numpy as np
from PIL import Image
from transformers import (
    SegformerImageProcessor,
    SegformerForSemanticSegmentation
)

# ─────────────────────────────────────
# MARK: — Model
# Fine-tuned on FoodSeg103 dataset
# 103 food ingredient categories
# ─────────────────────────────────────
MODEL_NAME = "LightDestory/segformer-b0-finetuned-segments-food-oct-24v2"

processor = None
model     = None

def load_model():
    global processor, model
    if model is None:
        print("⏳ Loading SegFormer food model...")
        processor = SegformerImageProcessor.from_pretrained(MODEL_NAME)
        model     = SegformerForSemanticSegmentation.from_pretrained(MODEL_NAME)
        model.eval()
        print("✅ SegFormer loaded successfully")

# ─────────────────────────────────────
# MARK: — Segment Food
# ─────────────────────────────────────
async def segment_food(image_bytes: bytes) -> list[dict]:
    """
    Segments food image into ingredient regions.
    Returns list of detected ingredients with
    their bounding boxes and coverage area.
    """
    try:
        load_model()

        # ── Load image ────────────────
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        orig_w, orig_h = image.size

        # ── Run SegFormer ─────────────
        inputs  = processor(images=image, return_tensors="pt")

        with torch.no_grad():
            outputs = model(**inputs)

        # ── Process logits ────────────
        logits = outputs.logits  # [1, num_labels, H, W]

        # Upsample to original image size
        upsampled = torch.nn.functional.interpolate(
            logits,
            size=(orig_h, orig_w),
            mode="bilinear",
            align_corners=False
        )

        # Get predicted class per pixel
        seg_map = upsampled.argmax(dim=1).squeeze().numpy()

        # ── Extract segments ──────────
        id2label   = model.config.id2label
        total_px   = orig_w * orig_h
        segments   = []
        seen_labels = set()

        for label_id, label_name in id2label.items():
            # Skip background
            if label_name.lower() in ["background", "other", "misc"]:
                continue

            # Find pixels for this label
            mask = (seg_map == label_id)
            pixel_count = mask.sum()

            # Skip if less than 2% of image
            area = pixel_count / total_px
            if area < 0.02:
                continue

            # Skip duplicates
            if label_name in seen_labels:
                continue
            seen_labels.add(label_name)

            # Get bounding box
            rows = np.any(mask, axis=1)
            cols = np.any(mask, axis=0)
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]

            # Normalise bbox to 0-1
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

        # Sort by area (largest first)
        segments.sort(key=lambda x: x["area"], reverse=True)

        # Return top 8 ingredients
        result = segments[:8]

        print(f"SegFormer found {len(result)} ingredients: "
              f"{[s['label'] for s in result]}")

        return result

    except Exception as e:
        print(f"SegFormer error: {e}")
        return []


# ─────────────────────────────────────
# MARK: — Format For Gemini
# Converts segments to text description
# for Gemini prompt enhancement
# ─────────────────────────────────────
def segments_to_description(segments: list[dict]) -> str:
    """
    Converts SegFormer output to a text
    description for Gemini prompt.
    """
    if not segments:
        return ""

    parts = []
    for seg in segments:
        pct  = int(seg["area"] * 100)
        parts.append(f"{seg['label']} ({pct}% of image)")

    return "Visible ingredients detected: " + ", ".join(parts)