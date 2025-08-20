from jose import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
import os
from ..models import User, License, LicenseType
from pydantic import BaseModel, EmailStr
import secrets
import string


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_access_token(self, user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {"user_id": user_id, "exp": expire, "iat": datetime.utcnow()}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[int]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get("user_id")
        except jwt.JWTError:
            return None

    def generate_license_key(self) -> str:
        chars = string.ascii_uppercase + string.digits
        parts = ["".join(secrets.choice(chars) for _ in range(4)) for _ in range(4)]
        return "-".join(parts)

    def create_user_with_license(self, db, user_data: UserCreate):
        if db.query(User).filter((User.email == user_data.email) | (User.username == user_data.username)).first():
            raise ValueError("User with this email or username already exists")

        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=self.hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        db.add(user)
        db.flush()

        license = License(
            user_id=user.id,
            license_type=LicenseType.FREE.value,
            license_key=self.generate_license_key(),
            max_file_size_mb=10,
            max_monthly_operations=100,
            expires_at=datetime.utcnow() + timedelta(days=365),
        )
        db.add(license)
        db.commit()
        db.refresh(user)
        return user

    def authenticate_user(self, db, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_active or not self.verify_password(password, user.hashed_password):
            return None
        return user
