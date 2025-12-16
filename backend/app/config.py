import os
from pathlib import Path
from typing import List


class Settings:
    APP_NAME: str = "Fuzzy Lookup"
    APP_VERSION: str = "1.0.0"
    
    ALLOWED_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:5173",
        ).split(",")
        if origin.strip()
    ] + [
        "https://fuzzylookupmatch.com",
        "http://fuzzylookupmatch.com",
        "https://api.fuzzylookupmatch.com",
        "http://api.fuzzylookupmatch.com"
    ]
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://fuzzy_user:fuzzy_password@localhost:5432/fuzzy_lookup",
    )
    
    DATA_DIR: Path = Path("data")
    UPLOADS_DIR: Path = DATA_DIR / "uploads"
    DOWNLOADS_DIR: Path = DATA_DIR / "downloads"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MAX_FILE_SIZE_MB: int = 100
    SUBSCRIPTION_COLLECTION: str = os.getenv("SUBSCRIPTION_COLLECTION", "payments")
    SUBSCRIPTION_DOC_IDS: List[str] = [
        item.strip()
        for item in os.getenv("SUBSCRIPTION_DOC_IDS", "Fuzzycloud").split(",")
        if item.strip()
    ]
    ADMIN_EMAILS: List[str] = [
        email.strip().lower()
        for email in os.getenv("ADMIN_EMAILS", "").split(",")
        if email.strip()
    ]
    DEFAULT_ADMIN_EMAILS: List[str] = [
        "kilelronos@gmail.com",
        "smallpdfkenya@gmail.com",
    ]

    def create_directories(self):
        self.DATA_DIR.mkdir(exist_ok=True)
        self.UPLOADS_DIR.mkdir(exist_ok=True)
        self.DOWNLOADS_DIR.mkdir(exist_ok=True)

    def get_admin_emails(self) -> List[str]:
        source = self.ADMIN_EMAILS or self.DEFAULT_ADMIN_EMAILS
        return [email.lower() for email in source]


settings = Settings()
