from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.services.license import LicenseService, LicenseInfo, LicenseUpgrade
from app.dependencies import get_current_user, get_license_service
from typing import Dict, Any, Optional

router = APIRouter()


@router.get("/info", response_model=Optional[LicenseInfo])
async def get_license_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_svc: LicenseService = Depends(get_license_service),
):
    return license_svc.get_license_info(current_user, db)


@router.get("/types")
async def get_license_types(license_svc: LicenseService = Depends(get_license_service)) -> Dict[str, Any]:
    return license_svc.get_license_types()


@router.post("/upgrade", response_model=LicenseInfo)
async def upgrade_license(
    license_upgrade: LicenseUpgrade,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_svc: LicenseService = Depends(get_license_service),
):
    new_license = license_svc.upgrade_license(current_user, license_upgrade, db)
    return LicenseInfo.model_validate(new_license)


@router.post("/validate/{license_key}")
async def validate_license_key(
    license_key: str, db: Session = Depends(get_db), license_svc: LicenseService = Depends(get_license_service)
):
    license = license_svc.validate_license_key(license_key, db)
    if license:
        return {
            "valid": True,
            "license_type": license.license_type,
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
            "max_file_size_mb": license.max_file_size_mb,
            "max_monthly_operations": license.max_monthly_operations,
        }
    return {"valid": False, "message": "Invalid or expired license key"}


@router.get("/usage")
async def get_license_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_svc: LicenseService = Depends(get_license_service),
):
    license = license_svc.get_user_active_license(current_user, db)

    if not license:
        raise HTTPException(status_code=404, detail="No active license found")

    usage_percentage = (license.current_month_operations / license.max_monthly_operations) * 100

    return {
        "license_type": license.license_type,
        "current_operations": license.current_month_operations,
        "max_operations": license.max_monthly_operations,
        "operations_remaining": license.operations_remaining,
        "usage_percentage": round(usage_percentage, 2),
        "max_file_size_mb": license.max_file_size_mb,
        "expires_at": license.expires_at.isoformat() if license.expires_at else None,
        "is_expired": license.is_expired,
    }
