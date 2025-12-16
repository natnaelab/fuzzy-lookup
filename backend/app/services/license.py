from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from google.cloud import firestore
from pydantic import BaseModel, Field

from ..config import settings
from ..core.subscriptions import DEFAULT_PLAN_ID, SubscriptionPlan
from ..models import User
from .subscription_plan import SubscriptionPlanService


class LicenseInfo(BaseModel):
    plan_id: str
    product: str
    display_name: str
    conversions_remaining: Optional[int]
    max_file_size_mb: int
    expiry: Optional[datetime]
    is_expired: bool
    paypal_link: Optional[str]


class LicenseUpgrade(BaseModel):
    plan_id: str = Field(alias="license_type")
    duration_months: int = 12

    class Config:
        populate_by_name = True


class SubscriptionRecord:
    def __init__(
        self,
        email: str,
        plan: SubscriptionPlan,
        conversions_remaining: Optional[int],
        expiry: Optional[datetime],
        doc_id: str,
        raw_entry: Optional[Dict[str, Any]] = None,
    ):
        self.email = email
        self.plan = plan
        self.conversions_remaining = conversions_remaining
        self.expiry = expiry
        self.doc_id = doc_id
        self.raw_entry: Dict[str, Any] = raw_entry or {}

    @property
    def is_expired(self) -> bool:
        if self.expiry is None:
            return False
        today = datetime.utcnow().date()
        return self.expiry.date() < today


def _parse_expiry(raw_value: Any) -> Optional[datetime]:
    if raw_value is None:
        return None

    if isinstance(raw_value, datetime):
        return raw_value

    if isinstance(raw_value, date):
        return datetime.combine(raw_value, datetime.min.time())

    if isinstance(raw_value, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                parsed = datetime.strptime(raw_value, fmt)
                return parsed
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(raw_value)
        except ValueError:
            return None

    return None


def _normalize_conversions(value: Any, plan: SubscriptionPlan) -> Optional[int]:
    if plan.max_conversions is None:
        return None

    if value is None:
        return plan.max_conversions

    try:
        conversions = int(value)
    except (TypeError, ValueError):
        return plan.max_conversions

    return max(conversions, 0)


class LicenseService:
    def __init__(
        self,
        client: Optional[firestore.Client] = None,
        plan_service: Optional[SubscriptionPlanService] = None,
    ):
        self.client = client or self._create_client()
        self.plan_service = plan_service or SubscriptionPlanService()
        self.collection_name = settings.SUBSCRIPTION_COLLECTION

        configured_ids = settings.SUBSCRIPTION_DOC_IDS or []
        plan_ids = {
            plan.doc_id for plan in self.plan_service.get_cached_plans(include_inactive=True).values()
        }

        doc_ids: List[str] = []
        for doc_id in configured_ids + list(plan_ids):
            if doc_id and doc_id not in doc_ids:
                doc_ids.append(doc_id)

        self.doc_ids = doc_ids or ["Fuzzycloud"]
        self.default_doc_id = self.doc_ids[0]

    def _create_client(self) -> firestore.Client:
        try:
            return firestore.Client()
        except Exception as exc:
            raise RuntimeError("Failed to create Firestore client") from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_user_active_license(self, user: User, db=None) -> Optional[SubscriptionRecord]:
        email = user.email.lower()
        return self._get_record(email)

    def check_file_upload_permissions(self, user: User, db, file_size_bytes: int):
        record = self._require_subscription(user)
        if record.is_expired:
            raise HTTPException(status_code=403, detail="Subscription has expired")

        size_mb = file_size_bytes / (1024 * 1024)
        if size_mb > record.plan.max_file_size_mb:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"File size ({size_mb:.2f}MB) exceeds plan limit of "
                    f"{record.plan.max_file_size_mb}MB"
                ),
            )

    def check_operation_permissions(self, user: User, db):
        record = self._require_subscription(user)

        if record.is_expired:
            raise HTTPException(status_code=403, detail="Subscription has expired")

        if record.plan.max_conversions is not None and (record.conversions_remaining or 0) <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Conversion limit reached for plan '{record.plan.display_name}'. "
                    "Please upgrade your subscription."
                ),
            )

    def increment_operation_count(self, user: User, db):
        record = self._require_subscription(user)
        if record.plan.max_conversions is None:
            return

        self._decrement_conversion(record)

    def upgrade_license(self, user: User, license_upgrade: LicenseUpgrade, db) -> LicenseInfo:
        plan = self._resolve_plan(license_upgrade.plan_id)

        duration_days = license_upgrade.duration_months * 30
        expiry = datetime.utcnow() + timedelta(days=duration_days)
        conversions = plan.max_conversions

        record = self._write_subscription(
            email=user.email.lower(),
            plan=plan,
            expiry=expiry,
            conversions=conversions,
            doc_id=plan.doc_id,
        )

        return self._record_to_info(record)

    def get_license_info(self, user: User, db) -> Optional[LicenseInfo]:
        record = self.get_user_active_license(user, db)
        if not record:
            return None
        return self._record_to_info(record)

    def get_license_types(self) -> Dict[str, Any]:
        plans = []
        for plan in self.plan_service.get_cached_plans().values():
            plans.append(
                {
                    "plan_id": plan.plan_id,
                    "product_name": plan.product_name,
                    "display_name": plan.display_name,
                    "description": plan.description,
                    "max_conversions": plan.max_conversions,
                    "max_file_size_mb": plan.max_file_size_mb,
                    "default_duration_days": plan.default_duration_days,
                    "paypal_link": plan.paypal_link,
                    "price_usd": plan.price_usd,
                }
            )
        return {"plans": plans}

    def ensure_default_subscription(self, user: User, plan_id: str = DEFAULT_PLAN_ID):
        email = user.email.lower()
        record = self._get_record(email)
        if record:
            return

        plan = self._resolve_plan(plan_id)
        expiry = datetime.utcnow() + timedelta(days=plan.default_duration_days)
        conversions = plan.max_conversions

        self._write_subscription(email=email, plan=plan, expiry=expiry, conversions=conversions)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_subscription(self, user: User) -> SubscriptionRecord:
        record = self.get_user_active_license(user)
        if not record:
            raise HTTPException(status_code=403, detail="Subscription not found for user")
        return record

    def _resolve_plan(self, identifier: str) -> SubscriptionPlan:
        return self.plan_service.get_plan(identifier)

    def _collection(self):
        return self.client.collection(self.collection_name)

    def _get_record(self, email: str) -> Optional[SubscriptionRecord]:
        for doc_id in self.doc_ids:
            doc_ref = self._collection().document(doc_id)
            snapshot = doc_ref.get()
            if not snapshot.exists:
                continue

            data = snapshot.to_dict() or {}
            entry = data.get(email)
            if not entry:
                continue

            plan = self._resolve_plan(entry.get("product", DEFAULT_PLAN_ID))
            conversions = _normalize_conversions(entry.get("conversions"), plan)
            expiry = _parse_expiry(entry.get("expiry"))

            return SubscriptionRecord(
                email=email,
                plan=plan,
                conversions_remaining=conversions,
                expiry=expiry,
                doc_id=doc_id,
                raw_entry=entry,
            )

        return None

    def _write_subscription(
        self,
        email: str,
        plan: SubscriptionPlan,
        expiry: Optional[datetime],
        conversions: Optional[int],
        doc_id: Optional[str] = None,
    ) -> SubscriptionRecord:
        doc_id = doc_id or plan.doc_id or self.default_doc_id
        doc_ref = self._collection().document(doc_id)

        expiry_value = expiry.date().isoformat() if expiry else None
        payload = {
            "product": plan.product_name,
            "expiry": expiry_value,
            "conversions": conversions,
        }

        doc_ref.set({email: payload}, merge=True)

        return SubscriptionRecord(
            email=email,
            plan=plan,
            conversions_remaining=_normalize_conversions(conversions, plan),
            expiry=_parse_expiry(expiry_value),
            doc_id=doc_id,
            raw_entry=payload,
        )

    def _decrement_conversion(self, record: SubscriptionRecord):
        doc_ref = self._collection().document(record.doc_id)

        @firestore.transactional
        def decrement(transaction: firestore.Transaction):
            snapshot = doc_ref.get(transaction=transaction)
            current_data = snapshot.to_dict() or {}
            entry = current_data.get(record.email) or {}

            plan = self._resolve_plan(entry.get("product", record.plan.plan_id))

            if plan.max_conversions is None:
                entry["conversions"] = None
            else:
                remaining = _normalize_conversions(entry.get("conversions"), plan)
                if remaining is None:
                    remaining = plan.max_conversions

                if remaining <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=(
                            f"Conversion limit reached for plan '{plan.display_name}'. "
                            "Please upgrade your subscription."
                        ),
                    )

                entry["conversions"] = remaining - 1

            transaction.set(doc_ref, {record.email: entry}, merge=True)

        transaction = self.client.transaction()
        decrement(transaction)

    def _record_to_info(self, record: SubscriptionRecord) -> LicenseInfo:
        return LicenseInfo(
            plan_id=record.plan.plan_id,
            product=record.plan.product_name,
            display_name=record.plan.display_name,
            conversions_remaining=record.conversions_remaining,
            max_file_size_mb=record.plan.max_file_size_mb,
            expiry=record.expiry,
            is_expired=record.is_expired,
            paypal_link=record.plan.paypal_link,
        )
