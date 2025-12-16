from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class SubscriptionPlan:
    plan_id: str
    product_name: str
    display_name: str
    max_conversions: Optional[int]
    max_file_size_mb: int
    default_duration_days: int
    description: Optional[str] = None
    paypal_link: Optional[str] = None
    price_usd: float = 0.0
    doc_id: str = "Fuzzycloud"
    is_active: bool = True


SUBSCRIPTION_PLANS: Dict[str, SubscriptionPlan] = {
    "free": SubscriptionPlan(
        plan_id="free",
        product_name="free",
        display_name="Free Plan",
        max_conversions=10,
        max_file_size_mb=2,
        default_duration_days=365,
        paypal_link=None,
        price_usd=0.0,
        doc_id="Fuzzycloud",
        is_active=True,
    ),
    "basic": SubscriptionPlan(
        plan_id="basic",
        product_name="Fuzzycloud-basic-plan",
        display_name="Fuzzycloud Basic Plan",
        max_conversions=50,
        max_file_size_mb=10,
        default_duration_days=30,
        paypal_link="https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-0KB98147CY755271SNDYPGNQ",
        price_usd=70.0,
        doc_id="Fuzzycloud",
        is_active=True,
    ),
    "standard": SubscriptionPlan(
        plan_id="standard",
        product_name="Fuzzycloud-standard-plan",
        display_name="Fuzzycloud Standard Plan",
        max_conversions=None,
        max_file_size_mb=50,
        default_duration_days=30,
        paypal_link="https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-88A51664YJ336081YNDSSZ4I",
        price_usd=150.0,
        doc_id="Fuzzycloud",
        is_active=True,
    ),
}


PLAN_BY_PRODUCT: Dict[str, SubscriptionPlan] = {
    plan.product_name: plan for plan in SUBSCRIPTION_PLANS.values()
}


DEFAULT_PLAN_ID = "free"
