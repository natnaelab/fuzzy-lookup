from sqlalchemy.orm import Session
from ..models import User, License, LicenseType
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import HTTPException
import secrets
import string


class LicenseInfo(BaseModel):
    id: int
    license_type: str
    license_key: Optional[str]
    is_active: bool
    max_file_size_mb: int
    max_monthly_operations: int
    current_month_operations: int
    operations_remaining: int
    is_expired: bool
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class LicenseUpgrade(BaseModel):
    license_type: str
    duration_months: int = 12


class LicenseService:
    LICENSE_CONFIGS = {
        LicenseType.FREE.value: {
            "max_file_size_mb": 10,
            "max_monthly_operations": 100
        },
        LicenseType.PREMIUM.value: {
            "max_file_size_mb": 100,
            "max_monthly_operations": 10000
        },
    }

    def get_user_active_license(self, user: User, db: Session) -> Optional[License]:
        return db.query(License).filter(License.user_id == user.id, License.is_active == True).first()

    def check_file_upload_permissions(self, user: User, db: Session, file_size_bytes: int):
        license = self.get_user_active_license(user, db)

        if not license:
            raise HTTPException(status_code=403, detail="No active license found")

        if license.is_expired:
            raise HTTPException(status_code=403, detail="License has expired")

        file_size_mb = file_size_bytes / (1024 * 1024)
        if file_size_mb > license.max_file_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({file_size_mb:.2f}MB) exceeds limit of {license.max_file_size_mb}MB",
            )

    def check_operation_permissions(self, user: User, db: Session):
        license = self.get_user_active_license(user, db)

        if not license:
            raise HTTPException(status_code=403, detail="No active license found")

        if license.is_expired:
            raise HTTPException(status_code=403, detail="License has expired")

        if license.operations_remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly operation limit of {license.max_monthly_operations} reached",
            )

    def increment_operation_count(self, user: User, db: Session):
        license = self.get_user_active_license(user, db)

        if license:
            license.current_month_operations += 1
            db.commit()

    def reset_monthly_operations(self, db: Session):
        db.query(License).update({License.current_month_operations: 0})
        db.commit()

    def generate_license_key(self) -> str:
        chars = string.ascii_uppercase + string.digits
        parts = ["".join(secrets.choice(chars) for _ in range(4)) for _ in range(4)]
        return "-".join(parts)

    def upgrade_license(self, user: User, license_upgrade: LicenseUpgrade, db: Session) -> License:
        if license_upgrade.license_type not in self.LICENSE_CONFIGS:
            raise ValueError("Invalid license type")

        current_license = self.get_user_active_license(user, db)
        if current_license:
            current_license.is_active = False

        config = self.LICENSE_CONFIGS[license_upgrade.license_type]
        new_license = License(
            user_id=user.id,
            license_type=license_upgrade.license_type,
            license_key=self.generate_license_key(),
            max_file_size_mb=config["max_file_size_mb"],
            max_monthly_operations=config["max_monthly_operations"],
            expires_at=datetime.utcnow() + timedelta(days=30 * license_upgrade.duration_months),
        )

        db.add(new_license)
        db.commit()
        db.refresh(new_license)
        return new_license

    def get_license_info(self, user: User, db: Session) -> Optional[LicenseInfo]:
        license = self.get_user_active_license(user, db)

        if not license:
            return None

        return LicenseInfo(
            id=license.id,
            license_type=license.license_type,
            license_key=license.license_key,
            is_active=license.is_active,
            max_file_size_mb=license.max_file_size_mb,
            max_monthly_operations=license.max_monthly_operations,
            current_month_operations=license.current_month_operations,
            operations_remaining=license.operations_remaining,
            is_expired=license.is_expired,
            expires_at=license.expires_at,
            created_at=license.created_at,
        )

    def get_license_types(self) -> Dict[str, Any]:
        return {
            "license_types": [
                {"type": license_type, "config": config} for license_type, config in self.LICENSE_CONFIGS.items()
            ]
        }

    def validate_license_key(self, license_key: str, db: Session) -> Optional[License]:
        license = db.query(License).filter(License.license_key == license_key, License.is_active == True).first()

        return license if license and not license.is_expired else None
