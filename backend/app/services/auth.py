from jose import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING
import os
from ..models import User
from pydantic import BaseModel, EmailStr

if TYPE_CHECKING:
    from .license import LicenseService


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

    def create_user_with_license(
        self,
        db,
        user_data: UserCreate,
        license_service: "LicenseService",
    ):
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

        db.commit()
        db.refresh(user)

        license_service.ensure_default_subscription(user)
        return user

    def authenticate_user(self, db, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_active or not self.verify_password(password, user.hashed_password):
            return None
        return user
