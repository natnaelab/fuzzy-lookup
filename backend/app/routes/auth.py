from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from urllib.parse import quote
import logging
from app.database import get_db
from app.services.auth import (
    AuthService,
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.email import EmailService
from app.services.license import LicenseService
from app.models import User
from app.config import settings
from app.dependencies import (
    get_auth_service,
    get_current_user,
    get_email_service,
    get_license_service,
)

router = APIRouter()
GENERIC_FORGOT_PASSWORD_MESSAGE = "If an account exists for this email, a password reset link has been sent."
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate, 
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    license_service: LicenseService = Depends(get_license_service),
):
    """Register a new user with a default free license"""
    try:
        user = auth_service.create_user_with_license(db, user_data, license_service)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin, 
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return access token"""
    user = auth_service.authenticate_user(db, user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(user.id)
    
    return Token(
        access_token=access_token,
        expires_in=auth_service.access_token_expire_minutes * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh user access token"""
    access_token = auth_service.create_access_token(current_user.id)
    
    return Token(
        access_token=access_token,
        expires_in=auth_service.access_token_expire_minutes * 60
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service),
):
    """Request a password reset link"""
    if not settings.is_development_env() and not email_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email service is not configured",
        )

    user = db.query(User).filter(
        User.email == request_data.email,
        User.is_active == True,  # noqa: E712
    ).first()

    if user:
        reset_token = auth_service.create_password_reset_token(user)
        reset_link = (
            f"{settings.FRONTEND_BASE_URL}/reset-password?token={quote(reset_token, safe='')}"
        )
        try:
            email_service.send_password_reset_email(
                to_email=user.email,
                reset_link=reset_link,
                expiry_minutes=auth_service.password_reset_token_expire_minutes,
            )
        except Exception:
            logger.exception(
                "Failed to send password reset email for user_id=%s", user.id
            )

    return MessageResponse(message=GENERIC_FORGOT_PASSWORD_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request_data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Reset user password using a reset token"""
    token_payload = auth_service.verify_password_reset_token(request_data.token)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user_id = token_payload.get("user_id")
    token_password_signature = token_payload.get("pwd_sig")
    if not user_id or not token_password_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True,  # noqa: E712
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    current_signature = auth_service._password_reset_signature(user)
    if current_signature != token_password_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if len(request_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long",
        )

    if auth_service.verify_password(request_data.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    user.hashed_password = auth_service.hash_password(request_data.new_password)
    db.commit()

    return MessageResponse(message="Password has been reset successfully.")
