---
title: FoodMind Backend
emoji: 🍽️
colorFrom: green
colorTo: yellow
sdk: docker
pinned: false
---

# FoodMind Backend ⚙️

> Real-time AI food analysis backend powering the [FoodMind iOS app](https://github.com/AhmadDurrani579/foodmind-ios)

[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![HuggingFace](https://img.shields.io/badge/Deployed-HuggingFace%20Spaces-yellow)](https://huggingface.co/spaces/ahmaddurrani-food-mind)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

<br>

## 🏗 Architecture

```
iOS App
   │
   │ WebSocket (JWT auth)
   ▼
FastAPI Server
   │
   ├── YOLOv8 ──────────────► Food detection + bounding box
   │
   ├── Gemini 2.5 Flash ────► Nutrition analysis + ingredient positions
   │        │
   │        └── Sensor Fusion ► Combined confidence score
   │
   ├── Sketchfab API ────────► Dynamic 3D model search + download
   │
   ├── Cloudinary ───────────► Permanent image + 3D model storage
   │
   └── PostgreSQL (Neon) ────► Users, scans, posts
```

<br>

## 🚀 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login + get JWT token |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `WS /ws/scan?token=JWT` | Real-time food scan pipeline |

**WebSocket message flow:**
```json
// iOS sends:
{
  "image": "base64_encoded_image",
  "mobilenet_hint": "pizza",
  "mobilenet_confidence": 0.94
}

// Backend returns:
{
  "type": "scan_result",
  "result": { "dish_name": "...", "calories": 780, ... },
  "validation": { "validation_level": "high", "final_confidence": 94 },
  "yolo": { "detected": true, "label": "pizza", "bbox_norm": [0.1, 0.2, 0.8, 0.7] },
  "model_3d": { "url": "https://cloudinary.com/...", "format": "usdz" },
  "image_url": "https://cloudinary.com/..."
}
```

### Scans
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/scans/me` | Get user scan history |
| GET | `/scans/stats/me` | Get nutrition stats |
| GET | `/scans/{id}` | Get single scan |
| DELETE | `/scans/{id}` | Delete scan |

### Posts (Social Feed)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/posts` | Share scan to feed |
| GET | `/posts/feed` | Get all posts |
| GET | `/posts/me` | Get my posts |
| POST | `/posts/{id}/like` | Like a post |
| DELETE | `/posts/{id}` | Delete post |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me` | Get profile |
| PUT | `/users/me` | Update profile |

<br>

## 🧠 AI Pipeline Detail

### 1. YOLOv8 — Food Detection
```python
# yolo_service.py
# Model: yolov8n.pt (nano — fastest on CPU)
# Returns: label, confidence, bounding box (normalised)
# Used for: AR anchor positioning + sensor fusion
```

### 2. Gemini 2.5 Flash — Nutrition Analysis
```python
# gemini_service.py
# Multi-key rotation (up to 6 API keys)
# Model fallback chain: gemini-2.5-flash → gemini-2.0-flash
# Returns: dish name, calories, macros, ingredients with positions,
#          recipe steps, allergens, health score
```

### 3. Sensor Fusion
```python
# Combines YOLO + Gemini confidence scores
# Same principle as autonomous vehicle sensor fusion
# Final confidence = (gemini_conf + yolo_conf) / 2
# Only fuses when YOLO detects a known food label
```

### 4. Sketchfab 3D Models
```python
# sketchfab_service.py
# Curated model UIDs for common foods (pizza, burger, sushi...)
# Dynamic search fallback for unknown foods
# Downloads USDZ/GLB → uploads to Cloudinary (permanent cache)
# iOS loads from Cloudinary URL — instant on repeat scans
```

<br>

## 🗄 Database Schema

```sql
-- Users
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR UNIQUE NOT NULL,
    username    VARCHAR UNIQUE NOT NULL,
    first_name  VARCHAR,
    password_hash TEXT NOT NULL,
    avatar_url  TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Scans
CREATE TABLE scans (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID REFERENCES users(id),
    dish_name           VARCHAR,
    cuisine             VARCHAR,
    calories            INTEGER,
    protein_g           FLOAT,
    carbs_g             FLOAT,
    fat_g               FLOAT,
    fiber_g             FLOAT,
    health_score        INTEGER,
    confidence          INTEGER,
    validation_level    VARCHAR,
    final_confidence    INTEGER,
    mobilenet_dish      VARCHAR,
    mobilenet_confidence FLOAT,
    gemini_dish         VARCHAR,
    ingredients         JSONB,
    recipe_steps        JSONB,
    tags                TEXT[],
    allergens           TEXT[],
    cooking_tip         TEXT,
    portion_size        VARCHAR,
    image_url           TEXT,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- Posts (Social Feed)
CREATE TABLE posts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    scan_id         UUID REFERENCES scans(id),
    caption         TEXT,
    image_url       TEXT,
    dish_name       VARCHAR,
    cuisine         VARCHAR,
    calories        INTEGER,
    protein_g       FLOAT,
    carbs_g         FLOAT,
    fat_g           FLOAT,
    health_score    INTEGER,
    tags            TEXT,
    likes_count     INTEGER DEFAULT 0,
    comments_count  INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

<br>

## 📁 Project Structure

```
foodmind-backend/
├── app/
│   ├── main.py                    # FastAPI app + router registration
│   ├── core/
│   │   ├── config.py              # Settings + environment variables
│   │   ├── security.py            # Password hashing
│   │   └── dependencies.py        # Auth dependencies
│   ├── auth/
│   │   └── jwt_handler.py         # JWT create + verify
│   ├── router/
│   │   ├── auth.py                # /auth endpoints
│   │   ├── users.py               # /users endpoints
│   │   ├── scan.py                # /scans endpoints
│   │   ├── posts.py               # /posts endpoints
│   │   └── websocket.py           # WebSocket scan handler
│   ├── services/
│   │   ├── gemini_service.py      # Gemini AI nutrition analysis
│   │   ├── yolo_service.py        # YOLOv8 food detection
│   │   ├── scan_service.py        # Main scan orchestrator
│   │   ├── sketchfab_service.py   # 3D model search + download
│   │   └── cloudinary_service.py  # Image + model upload
│   └── db/
│       ├── database.py            # SQLAlchemy engine + session
│       ├── models_user.py         # User table model
│       ├── models_scan.py         # Scan table model
│       └── models_post.py         # Post table model
├── Dockerfile
└── requirements.txt
```

<br>

## 🔧 Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@host/dbname

# Auth
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256

# Gemini AI (supports up to 6 keys for rotation)
GEMINI_API_KEY_1=your_key_1
GEMINI_API_KEY_2=your_key_2
GEMINI_API_KEY_3=your_key_3

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret

# Sketchfab
SKETCHFAB_TOKEN=your_token
```

<br>

## 🐳 Local Setup

```bash
git clone https://github.com/AhmadDurrani579/foodmind
cd foodmind

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Fill in your credentials

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 7860

# API docs available at:
# http://localhost:7860/docs
```

<br>

## 🚀 Deployment (HuggingFace Spaces)

The backend is deployed on HuggingFace Spaces using Docker.

```dockerfile
FROM python:3.10-slim

# Install PyTorch CPU (for YOLOv8)
RUN pip install torch==2.4.0+cpu torchvision==0.19.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

**Add secrets in HuggingFace Space settings** — never commit `.env` files.

<br>

## 🔑 Multi-Key Gemini Rotation

To handle rate limits, the backend rotates through multiple Gemini API keys automatically:

```python
# If key 1 hits rate limit → switches to key 2 → key 3...
# Model fallback: gemini-2.5-flash → gemini-2.0-flash
# Each key gets its own free tier quota
```

Get free API keys at [aistudio.google.com](https://aistudio.google.com)

<br>

## 📦 Key Dependencies

```
fastapi          — REST API + WebSocket
uvicorn          — ASGI server
sqlalchemy       — ORM
psycopg2-binary  — PostgreSQL driver
python-jose      — JWT tokens
bcrypt           — Password hashing
ultralytics      — YOLOv8
google-genai     — Gemini AI
cloudinary       — Image storage
httpx            — Async HTTP (Sketchfab)
Pillow           — Image processing
```

<br>

## 🔗 Related

- **iOS App:** [github.com/AhmadDurrani579/foodmind-ios](https://github.com/AhmadDurrani579/foodmind-ios)
- **Live Demo:** [YouTube Short](https://youtube.com/shorts/-IEH7jZxJ8Q)
- **Deployed API:** [ahmaddurrani-food-mind.hf.space](https://ahmaddurrani-food-mind.hf.space)

<br>

## 👤 Author

**Ahmad Durrani** — Senior iOS Engineer / ML Engineer

- MSc Computer Vision, Robotics & ML — University of Surrey
- Google WebRTC contributor • OpenCV contributor
- [LinkedIn](https://www.linkedin.com/in/ahmad-yar-98990690/) • [GitHub](https://github.com/AhmadDurrani579)

<br>

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Part of the FoodMind project — Point. Think. Know.*
