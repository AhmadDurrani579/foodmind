from pydantic_settings import BaseSettings
 
class Settings(BaseSettings):
 
    # ── Auth ──────────────────────────
    JWT_SECRET:    str = "change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30
 
    # ── Gemini ────────────────────────
    GEMINI_API_KEY: str = ""
 
    # ── Database ──────────────────────
    DATABASE_URL: str = ""
 
    # ── External APIs ─────────────────
    # SKETCHFAB_TOKEN: str = ""
    # MESHY_API_KEY:   str = ""
 
    class Config:
        env_file = ".env"
 
settings = Settings()
 








