#
# yolo_service.py
# FoodMind Backend
#
# app/services/yolo_service.py
#

import io
import time
from PIL import Image

# ── Lazy globals ──────────────────────
yolo_model = None

# ─────────────────────────────────────
# MARK: — Load Model
# ─────────────────────────────────────
def load_yolo():
    global yolo_model
    if yolo_model is not None:
        return True

    try:
        from ultralytics import YOLO
        print("⏳ Loading YOLOv8 model...")

        # YOLOv8n — smallest, fastest, works on CPU
        yolo_model = YOLO("yolov8n.pt")
        print("✅ YOLOv8 loaded successfully")
        return True

    except Exception as e:
        print(f"❌ YOLO load failed: {e}")
        yolo_model = None
        return False


# ─────────────────────────────────────
# MARK: — Detect Food
# Returns bounding box of main food item
# ─────────────────────────────────────
async def detect_food(image_bytes: bytes) -> dict:
    """
    Detects food/objects in image using YOLOv8.
    Returns:
    {
        "detected": True/False,
        "label": "pizza",
        "confidence": 0.94,
        "bbox": [x1, y1, x2, y2],        # pixel coords
        "bbox_norm": [x, y, w, h],        # normalised 0-1
        "all_detections": [...]
    }
    """
    try:
        if not load_yolo():
            return _empty_detection()

        # Load image
        image  = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = image.size

        # Run YOLO inference
        start   = time.time()
        results = yolo_model(image, verbose=False)
        elapsed = round(time.time() - start, 2)

        if not results or len(results) == 0:
            return _empty_detection()

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return _empty_detection()

        # Get all detections
        all_detections = []
        names = results[0].names

        for box in boxes:
            conf     = float(box.conf[0])
            cls_id   = int(box.cls[0])
            label    = names.get(cls_id, "unknown")
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            all_detections.append({
                "label":      label,
                "confidence": round(conf, 3),
                "bbox":       [round(x1), round(y1), round(x2), round(y2)],
                "bbox_norm":  [
                    round(x1 / width, 3),
                    round(y1 / height, 3),
                    round((x2 - x1) / width, 3),
                    round((y2 - y1) / height, 3)
                ]
            })

        # Sort by confidence
        all_detections.sort(
            key=lambda x: x["confidence"],
            reverse=True
        )

        if not all_detections:
            return _empty_detection()

        # Primary detection = highest confidence
        primary = all_detections[0]

        print(f"✅ YOLO detected: {primary['label']} "
              f"({int(primary['confidence'] * 100)}%) "
              f"in {elapsed}s")

        return {
            "detected":       True,
            "label":          primary["label"],
            "confidence":     primary["confidence"],
            "bbox":           primary["bbox"],
            "bbox_norm":      primary["bbox_norm"],
            "all_detections": all_detections[:5],  # top 5
            "inference_time": elapsed
        }

    except Exception as e:
        print(f"❌ YOLO error: {e}")
        return _empty_detection()


# ─────────────────────────────────────
# MARK: — Empty Detection
# ─────────────────────────────────────
def _empty_detection() -> dict:
    return {
        "detected":       False,
        "label":          "unknown",
        "confidence":     0.0,
        "bbox":           [],
        "bbox_norm":      [],
        "all_detections": [],
        "inference_time": 0.0
    }


# ─────────────────────────────────────
# MARK: — Calorie Estimate
# Basic calorie estimate from YOLO
# Used as fallback if Gemini fails
# ─────────────────────────────────────
YOLO_CALORIE_ESTIMATES = {
    "pizza":     800,
    "burger":    650,
    "hot dog":   350,
    "sandwich":  450,
    "salad":     200,
    "cake":      450,
    "donut":     350,
    "apple":     80,
    "banana":    110,
    "orange":    85,
    "broccoli":  55,
    "carrot":    52,
    "bowl":      400,
    "cup":       50,
    "bottle":    0,
    "fork":      0,
    "knife":     0,
    "spoon":     0,
}

def estimate_calories(label: str) -> int:
    label_lower = label.lower()
    for food, calories in YOLO_CALORIE_ESTIMATES.items():
        if food in label_lower:
            return calories
    return 400  # default estimate