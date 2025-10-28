import os
from pathlib import Path
from typing import List, Optional


class Settings:
    APP_NAME: str = "Fuzzy Lookup"
    APP_VERSION: str = "1.0.0"
    
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fuzzy_app.db")
    
    DATA_DIR: Path = Path("data")
    UPLOADS_DIR: Path = DATA_DIR / "uploads"
    DOWNLOADS_DIR: Path = DATA_DIR / "downloads"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MAX_FILE_SIZE_MB: int = 100
    FIRESTORE_PROJECT_ID: Optional[str] = os.getenv("FIRESTORE_PROJECT_ID")
    SUBSCRIPTION_COLLECTION: str = os.getenv("SUBSCRIPTION_COLLECTION", "payments")
    SUBSCRIPTION_DOC_IDS: List[str] = [
        item.strip()
        for item in os.getenv("SUBSCRIPTION_DOC_IDS", "Fuzzycloud").split(",")
        if item.strip()
    ]
    
    def create_directories(self):
        self.DATA_DIR.mkdir(exist_ok=True)
        self.UPLOADS_DIR.mkdir(exist_ok=True)
        self.DOWNLOADS_DIR.mkdir(exist_ok=True)


settings = Settings()
