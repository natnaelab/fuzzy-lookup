from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import (
    get_subscription_plan_service,
    require_admin_user,
)
from app.models import User
from app.services.subscription_plan import (
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
    SubscriptionPlanService,
    SubscriptionPlanUpdate,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/subscription-plans",
    response_model=List[SubscriptionPlanResponse],
)
async def list_subscription_plans(
    include_inactive: bool = True,
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    plan_service: SubscriptionPlanService = Depends(get_subscription_plan_service),
):
    return plan_service.list_plans(db, include_inactive=include_inactive)


@router.post(
    "/subscription-plans",
    response_model=SubscriptionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription_plan(
    payload: SubscriptionPlanCreate,
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    plan_service: SubscriptionPlanService = Depends(get_subscription_plan_service),
):
    try:
        return plan_service.create_plan(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put(
    "/subscription-plans/{plan_id}",
    response_model=SubscriptionPlanResponse,
)
async def update_subscription_plan(
    plan_id: str,
    payload: SubscriptionPlanUpdate,
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    plan_service: SubscriptionPlanService = Depends(get_subscription_plan_service),
):
    try:
        return plan_service.update_plan(db, plan_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/subscription-plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subscription_plan(
    plan_id: str,
    _: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
    plan_service: SubscriptionPlanService = Depends(get_subscription_plan_service),
):
    try:
        plan_service.delete_plan(db, plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
