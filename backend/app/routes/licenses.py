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
    return license_svc.upgrade_license(current_user, license_upgrade, db)


@router.get("/usage")
async def get_license_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    license_svc: LicenseService = Depends(get_license_service),
):
    record = license_svc.get_user_active_license(current_user, db)

    if not record:
        raise HTTPException(status_code=404, detail="No active license found")

    plan = record.plan
    remaining = record.conversions_remaining
    max_conversions = plan.max_conversions

    if max_conversions and remaining is not None:
        used = max_conversions - remaining
        usage_percentage = round((used / max_conversions) * 100, 2)
    else:
        usage_percentage = None

    return {
        "plan_id": plan.plan_id,
        "product_name": plan.product_name,
        "display_name": plan.display_name,
        "conversions_remaining": remaining,
        "max_conversions": max_conversions,
        "usage_percentage": usage_percentage,
        "max_file_size_mb": plan.max_file_size_mb,
        "expires_at": record.expiry.isoformat() if record.expiry else None,
        "is_expired": record.is_expired,
    }
