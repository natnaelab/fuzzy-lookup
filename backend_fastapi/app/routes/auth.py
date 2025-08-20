from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth import AuthService, UserCreate, UserLogin, Token, UserResponse
from app.models import User
from app.dependencies import get_current_user, get_auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate, 
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user with a default free license"""
    try:
        user = auth_service.create_user_with_license(db, user_data)
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
