from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.router.auth import router as auth_router
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.router import users


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
def root():
    return {"message": "FoodMind API is running"}


app.include_router(auth_router)
app.include_router(users.router)
