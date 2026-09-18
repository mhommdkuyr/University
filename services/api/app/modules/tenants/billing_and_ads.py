from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()

class SubscriptionPlan(BaseModel):
    tier: str  # starter, growth, enterprise
    active_user_rate: float
    included_ai_credits: int
    included_storage_gb: int

class UsageBillingReport(BaseModel):
    tenant_id: str
    active_students_count: int
    ai_credits_used: int
    storage_used_gb: float
    total_amount_due: float
    currency: str = "USD"

class Announcement(BaseModel):
    id: str
    title: str
    content: str
    target_role: Optional[str] = None
    priority: str = "normal"  # normal, urgent

class AdSetting(BaseModel):
    ads_enabled: bool = True
    max_frequency_per_user_day: int = 3
    revenue_share_percentage: float = 70.0

@router.get("/billing/plan", response_model=SubscriptionPlan)
async def get_billing_plan(request: Request):
    return SubscriptionPlan(
        tier="growth",
        active_user_rate=1.50,
        included_ai_credits=50000,
        included_storage_gb=500
    )

@router.get("/billing/usage", response_model=UsageBillingReport)
async def get_usage_report(request: Request):
    tenant_id = getattr(request.state, "tenant_id", "default")
    return UsageBillingReport(
        tenant_id=tenant_id,
        active_students_count=1200,
        ai_credits_used=14500,
        storage_used_gb=120.5,
        total_amount_due=1800.00
    )

@router.get("/announcements", response_model=List[Announcement])
async def list_announcements(request: Request):
    return [
        Announcement(id="anc_1", title="Welcome to Fall Semester 2026", content="Classes begin on Sunday.", priority="urgent")
    ]

@router.get("/ads/policy", response_model=AdSetting)
async def get_ad_policy(request: Request):
    return AdSetting(ads_enabled=True, max_frequency_per_user_day=3, revenue_share_percentage=70.0)
