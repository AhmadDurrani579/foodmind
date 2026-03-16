from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI( title="FoodMind Backend API",
               description="API for FoodMind backend services",
               version="1.0.0" )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health():
    return {
        "status": "ok",
        "app": "FoodMind Backend",
        "version": "1.0.0"
    }
