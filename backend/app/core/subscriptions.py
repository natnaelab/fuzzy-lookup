import json
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from app.config import settings


@dataclass(frozen=True)
class SubscriptionPlan:
    plan_id: str
    product_name: str
    display_name: str
    max_conversions: Optional[int]
    max_file_size_mb: int
    default_duration_days: int
    paypal_link: Optional[str] = None
    doc_id: str = "Fuzzycloud"


DEFAULT_PLAN_ID = "free"

_DEFAULT_PLAN_DATA: List[Dict[str, Any]] = [
    {
        "plan_id": "free",
        "product_name": "free",
        "display_name": "Free Plan",
        "max_conversions": 10,
        "max_file_size_mb": 2,
        "default_duration_days": 365,
        "paypal_link": None,
        "doc_id": "Fuzzycloud",
    },
    {
        "plan_id": "basic",
        "product_name": "Fuzzycloud-basic-plan",
        "display_name": "Fuzzycloud Basic Plan",
        "max_conversions": 50,
        "max_file_size_mb": 10,
        "default_duration_days": 30,
        "paypal_link": "https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-0KB98147CY755271SNDYPGNQ",
        "doc_id": "Fuzzycloud",
    },
    {
        "plan_id": "standard",
        "product_name": "Fuzzycloud-standard-plan",
        "display_name": "Fuzzycloud Standard Plan",
        "max_conversions": None,
        "max_file_size_mb": 50,
        "default_duration_days": 30,
        "paypal_link": "https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-88A51664YJ336081YNDSSZ4I",
        "doc_id": "Fuzzycloud",
    },
]

_plan_cache: Dict[str, SubscriptionPlan] = {}
_plan_lock = RLock()


def _plan_config_path() -> Path:
    return settings.PLAN_CONFIG_PATH


def _deserialize_plan(entry: Dict[str, Any]) -> SubscriptionPlan:
    return SubscriptionPlan(
        plan_id=entry["plan_id"],
        product_name=entry["product_name"],
        display_name=entry["display_name"],
        max_conversions=entry.get("max_conversions"),
        max_file_size_mb=entry["max_file_size_mb"],
        default_duration_days=entry["default_duration_days"],
        paypal_link=entry.get("paypal_link"),
        doc_id=entry.get("doc_id") or "Fuzzycloud",
    )


def _write_plan_file(plans: List[Dict[str, Any]]):
    path = _plan_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plans, indent=2))


def _read_plan_file() -> List[Dict[str, Any]]:
    path = _plan_config_path()
    if not path.exists():
        _write_plan_file(_DEFAULT_PLAN_DATA)
    try:
        raw = json.loads(path.read_text())
        if isinstance(raw, list):
            return raw
    except json.JSONDecodeError:
        pass
    # Fall back to defaults if file is corrupt
    _write_plan_file(_DEFAULT_PLAN_DATA)
    return _DEFAULT_PLAN_DATA


def _load_plans_from_file() -> Dict[str, SubscriptionPlan]:
    entries = _read_plan_file()
    plans: Dict[str, SubscriptionPlan] = {}
    for entry in entries:
        try:
            plan = _deserialize_plan(entry)
            plans[plan.plan_id] = plan
        except KeyError:
            # Skip invalid entries
            continue
    if not plans:
        plans = {item["plan_id"]: _deserialize_plan(item) for item in _DEFAULT_PLAN_DATA}
    return plans


def get_subscription_plans(force_reload: bool = False) -> Dict[str, SubscriptionPlan]:
    global _plan_cache
    with _plan_lock:
        if force_reload or not _plan_cache:
            _plan_cache = _load_plans_from_file()
        return dict(_plan_cache)


def get_plan_list(force_reload: bool = False) -> List[SubscriptionPlan]:
    return list(get_subscription_plans(force_reload).values())


def get_plan_by_product_map(force_reload: bool = False) -> Dict[str, SubscriptionPlan]:
    plans = get_subscription_plans(force_reload)
    return {plan.product_name: plan for plan in plans.values()}


def serialize_plan(plan: SubscriptionPlan) -> Dict[str, Any]:
    return asdict(plan)


def plan_from_dict(data: Dict[str, Any]) -> SubscriptionPlan:
    return _deserialize_plan(data)


def save_subscription_plans(plans: Dict[str, SubscriptionPlan]):
    entries = [serialize_plan(plan) for plan in plans.values()]
    _write_plan_file(entries)
    # Refresh cache
    get_subscription_plans(force_reload=True)


def upsert_subscription_plan(plan: SubscriptionPlan):
    plans = get_subscription_plans()
    plans[plan.plan_id] = plan
    save_subscription_plans(plans)


def delete_subscription_plan(plan_id: str):
    plans = get_subscription_plans()
    if plan_id in plans:
        del plans[plan_id]
        save_subscription_plans(plans)
