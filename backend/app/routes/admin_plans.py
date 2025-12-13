from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import List, Optional

from app.config import settings
from app.dependencies import get_current_user, get_license_service
from app.models import User
from app.services.license import LicenseService
from app.core.subscriptions import (
    DEFAULT_PLAN_ID,
    SubscriptionPlan,
    delete_subscription_plan,
    get_plan_list,
    get_subscription_plans,
    plan_from_dict,
    serialize_plan,
    upsert_subscription_plan,
)

router = APIRouter(prefix="/admin/plans", tags=["Plan Administration"])


def require_plan_admin(current_user: User = Depends(get_current_user)) -> User:
    allowed = settings.PLAN_ADMIN_EMAILS
    if not allowed or current_user.email.lower() not in allowed:
        raise HTTPException(status_code=403, detail="Not authorized to manage plans")
    return current_user


class PlanBase(BaseModel):
    product_name: str = Field(..., max_length=200)
    display_name: str = Field(..., max_length=200)
    max_conversions: Optional[int] = Field(None, ge=0)
    max_file_size_mb: int = Field(..., gt=0)
    default_duration_days: int = Field(..., gt=0)
    paypal_link: Optional[str] = Field(None, max_length=500)
    doc_id: Optional[str] = Field(default="Fuzzycloud", max_length=200)

    @validator("paypal_link")
    def empty_string_to_none(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value.strip() == "":
            return None
        return value


class PlanCreate(PlanBase):
    plan_id: str = Field(..., max_length=100)


class PlanUpdate(BaseModel):
    product_name: Optional[str] = Field(None, max_length=200)
    display_name: Optional[str] = Field(None, max_length=200)
    max_conversions: Optional[int] = Field(None, ge=0)
    max_file_size_mb: Optional[int] = Field(None, gt=0)
    default_duration_days: Optional[int] = Field(None, gt=0)
    paypal_link: Optional[str] = Field(None, max_length=500)
    doc_id: Optional[str] = Field(None, max_length=200)

    @validator("paypal_link")
    def empty_string_to_none(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value.strip() == "":
            return None
        return value


class PlanResponse(PlanBase):
    plan_id: str

    class Config:
        orm_mode = True


def _update_plan_instance(plan: SubscriptionPlan, updates: PlanUpdate) -> SubscriptionPlan:
    data = serialize_plan(plan)
    update_data = updates.dict(exclude_unset=True)
    data.update(update_data)
    data["plan_id"] = plan.plan_id  # prevent renaming
    return plan_from_dict(data)


@router.get("/", response_model=List[PlanResponse])
def list_plans(
    _: User = Depends(require_plan_admin),
) -> List[PlanResponse]:
    return [PlanResponse(**serialize_plan(plan)) for plan in get_plan_list()]


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: PlanCreate,
    _: User = Depends(require_plan_admin),
    license_service: LicenseService = Depends(get_license_service),
) -> PlanResponse:
    plans = get_subscription_plans()
    if payload.plan_id in plans:
        raise HTTPException(status_code=400, detail="Plan ID already exists")

    plan = plan_from_dict(payload.dict())
    upsert_subscription_plan(plan)
    license_service.refresh_plan_cache()

    return PlanResponse(**serialize_plan(plan))


@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: str,
    updates: PlanUpdate,
    _: User = Depends(require_plan_admin),
    license_service: LicenseService = Depends(get_license_service),
) -> PlanResponse:
    plans = get_subscription_plans()
    if plan_id not in plans:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan = _update_plan_instance(plans[plan_id], updates)
    upsert_subscription_plan(plan)
    license_service.refresh_plan_cache()

    return PlanResponse(**serialize_plan(plan))


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: str,
    _: User = Depends(require_plan_admin),
    license_service: LicenseService = Depends(get_license_service),
):
    if plan_id == DEFAULT_PLAN_ID:
        raise HTTPException(status_code=400, detail="Cannot delete the default plan")

    plans = get_subscription_plans()
    if plan_id not in plans:
        raise HTTPException(status_code=404, detail="Plan not found")

    delete_subscription_plan(plan_id)
    license_service.refresh_plan_cache()
