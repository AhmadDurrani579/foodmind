from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.router import websocket, scan, auth, users
import os

app = FastAPI(
    title="FoodMind Backend API",
    description="API for FoodMind backend services",
    version="1.0.0"
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FoodMind API is running"}

# ── Routers ──────────────────────────
app.include_router(auth.router)      # ← only once
app.include_router(users.router)
app.include_router(websocket.router)
app.include_router(scan.router)