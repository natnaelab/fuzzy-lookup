from functools import lru_cache
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .services.auth import AuthService
from .services.fuzzy import FuzzyService
from .services.license import LicenseService
from .services.file import FileService
from .services.subscription_plan import SubscriptionPlanService
from .config import settings

security = HTTPBearer()


@lru_cache()
def get_auth_service() -> AuthService:
    return AuthService()


@lru_cache()
def get_fuzzy_service() -> FuzzyService:
    return FuzzyService(get_file_service())


@lru_cache()
def get_subscription_plan_service() -> SubscriptionPlanService:
    return SubscriptionPlanService()


@lru_cache()
def get_license_service() -> LicenseService:
    return LicenseService(plan_service=get_subscription_plan_service())


@lru_cache()
def get_file_service() -> FileService:
    return FileService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    user_id = auth_service.verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.email and current_user.email.lower() in settings.get_admin_emails():
        return current_user
    raise HTTPException(status_code=403, detail="Admin access required")
