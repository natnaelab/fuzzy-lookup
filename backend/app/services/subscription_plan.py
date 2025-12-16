from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.subscriptions import DEFAULT_PLAN_ID, SUBSCRIPTION_PLANS, SubscriptionPlan
from ..database import SessionLocal
from ..models import SubscriptionPlan as SubscriptionPlanModel


class SubscriptionPlanBase(BaseModel):
    display_name: str
    product_name: str
    description: Optional[str] = None
    price_usd: float = Field(0.0, ge=0)
    max_conversions: Optional[int] = None
    max_file_size_mb: int = Field(..., gt=0)
    default_duration_days: int = Field(..., gt=0)
    paypal_link: Optional[str] = None
    doc_id: str = "Fuzzycloud"
    is_active: bool = True


class SubscriptionPlanCreate(SubscriptionPlanBase):
    plan_id: str = Field(..., min_length=2)


class SubscriptionPlanUpdate(BaseModel):
    display_name: Optional[str] = None
    product_name: Optional[str] = None
    description: Optional[str] = None
    price_usd: Optional[float] = Field(None, ge=0)
    max_conversions: Optional[int] = Field(None, ge=0)
    max_file_size_mb: Optional[int] = Field(None, gt=0)
    default_duration_days: Optional[int] = Field(None, gt=0)
    paypal_link: Optional[str] = None
    doc_id: Optional[str] = None
    is_active: Optional[bool] = None


class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: int
    plan_id: str

    class Config:
        from_attributes = True


class SubscriptionPlanService:
    def __init__(self):
        self._plan_cache: Dict[str, SubscriptionPlan] = {k: v for k, v in SUBSCRIPTION_PLANS.items()}
        self._product_cache: Dict[str, SubscriptionPlan] = {
            plan.product_name: plan for plan in SUBSCRIPTION_PLANS.values()
        }
        self.refresh_cache()

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def refresh_cache(self, db: Optional[Session] = None):
        session = db or SessionLocal()
        close_session = db is None
        try:
            plans = (
                session.query(SubscriptionPlanModel)
                .order_by(SubscriptionPlanModel.id.asc())
                .all()
            )
            if not plans:
                self._seed_defaults(session)
                plans = (
                    session.query(SubscriptionPlanModel)
                    .order_by(SubscriptionPlanModel.id.asc())
                    .all()
                )
            self._set_cache_from_models(plans)
        except Exception:
            self._plan_cache = {k: v for k, v in SUBSCRIPTION_PLANS.items()}
            self._product_cache = {
                plan.product_name: plan for plan in SUBSCRIPTION_PLANS.values()
            }
        finally:
            if close_session:
                session.close()

    def _set_cache_from_models(self, records: List[SubscriptionPlanModel]):
        if not records:
            self._plan_cache = {k: v for k, v in SUBSCRIPTION_PLANS.items()}
            self._product_cache = {
                plan.product_name: plan for plan in SUBSCRIPTION_PLANS.values()
            }
            return

        plan_map: Dict[str, SubscriptionPlan] = {}
        product_map: Dict[str, SubscriptionPlan] = {}
        for record in records:
            plan = SubscriptionPlan(
                plan_id=record.plan_id,
                product_name=record.product_name,
                display_name=record.display_name,
                description=record.description,
                max_conversions=record.max_conversions,
                max_file_size_mb=record.max_file_size_mb,
                default_duration_days=record.default_duration_days,
                paypal_link=record.paypal_link,
                price_usd=record.price_usd or 0.0,
                doc_id=record.doc_id or "Fuzzycloud",
                is_active=bool(record.is_active),
            )
            plan_map[plan.plan_id] = plan
            product_map[plan.product_name] = plan

        self._plan_cache = plan_map
        self._product_cache = product_map

    def _seed_defaults(self, db: Session):
        existing = {
            row.plan_id
            for row in db.query(SubscriptionPlanModel.plan_id).all()
        }
        created = False
        for plan in SUBSCRIPTION_PLANS.values():
            if plan.plan_id in existing:
                continue
            db.add(
                SubscriptionPlanModel(
                    plan_id=plan.plan_id,
                    product_name=plan.product_name,
                    display_name=plan.display_name,
                    max_conversions=plan.max_conversions,
                    max_file_size_mb=plan.max_file_size_mb,
                    default_duration_days=plan.default_duration_days,
                    paypal_link=plan.paypal_link,
                    price_usd=plan.price_usd,
                    doc_id=plan.doc_id,
                )
            )
            created = True
        if created:
            db.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_cached_plans(self, include_inactive: bool = False) -> Dict[str, SubscriptionPlan]:
        if include_inactive:
            return dict(self._plan_cache)
        return {k: v for k, v in self._plan_cache.items() if v.is_active}

    def get_plan(self, identifier: str) -> SubscriptionPlan:
        if identifier in self._plan_cache:
            return self._plan_cache[identifier]
        if identifier in self._product_cache:
            return self._product_cache[identifier]
        return self._plan_cache.get(DEFAULT_PLAN_ID) or SUBSCRIPTION_PLANS[DEFAULT_PLAN_ID]

    def list_plans(self, db: Session, include_inactive: bool = False) -> List[SubscriptionPlanResponse]:
        query = db.query(SubscriptionPlanModel)
        if not include_inactive:
            query = query.filter(SubscriptionPlanModel.is_active == True)  # noqa: E712
        records = query.order_by(SubscriptionPlanModel.id.asc()).all()
        return [SubscriptionPlanResponse.model_validate(record) for record in records]

    def create_plan(self, db: Session, payload: SubscriptionPlanCreate) -> SubscriptionPlanResponse:
        existing = (
            db.query(SubscriptionPlanModel)
            .filter(
                (SubscriptionPlanModel.plan_id == payload.plan_id)
                | (SubscriptionPlanModel.product_name == payload.product_name)
            )
            .first()
        )
        if existing:
            raise ValueError("Plan with this ID or product already exists")

        plan = SubscriptionPlanModel(**payload.model_dump())
        db.add(plan)
        db.commit()
        db.refresh(plan)
        self.refresh_cache(db)
        return SubscriptionPlanResponse.model_validate(plan)

    def update_plan(self, db: Session, plan_id: str, payload: SubscriptionPlanUpdate) -> SubscriptionPlanResponse:
        plan = (
            db.query(SubscriptionPlanModel)
            .filter(SubscriptionPlanModel.plan_id == plan_id)
            .first()
        )
        if not plan:
            raise ValueError("Plan not found")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)

        db.commit()
        db.refresh(plan)
        self.refresh_cache(db)
        return SubscriptionPlanResponse.model_validate(plan)

    def delete_plan(self, db: Session, plan_id: str):
        plan = (
            db.query(SubscriptionPlanModel)
            .filter(SubscriptionPlanModel.plan_id == plan_id)
            .first()
        )
        if not plan:
            raise ValueError("Plan not found")

        plan.is_active = False
        db.commit()
        self.refresh_cache(db)
