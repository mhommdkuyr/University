from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class FeatureDescriptor(BaseModel):
    feature_key: str
    enabled: bool
    integration_mode: str
    existing_page_detected: bool = False
    external_endpoint: Optional[str] = None


class EnvironmentDiscovery(BaseModel):
    tenant_id: str
    discovered_pages: List[str]
    discovered_features: List[str]
    recommended_actions: List[str]


class FeatureActivation(BaseModel):
    feature_key: str
    enabled: bool
    integration_mode: str = "platform"
    external_endpoint: Optional[str] = None


SUPPORTED_FEATURES = {
    "attendance": "الحضور والغياب",
    "schedule": "الجداول",
    "lectures": "المحاضرات والمواد التعليمية",
    "news": "الأخبار والإعلانات",
    "public_projects": "المشاريع العامة",
    "ai_assistant": "مساعد الذكاء الاصطناعي",
    "requests": "الخدمات والطلبات",
    "campus_map": "خريطة الحرم",
}


@router.get("/catalog", response_model=List[FeatureDescriptor])
async def feature_catalog() -> List[FeatureDescriptor]:
    return [
        FeatureDescriptor(feature_key=key, enabled=False, integration_mode="platform")
        for key in SUPPORTED_FEATURES
    ]


@router.post("/discover", response_model=EnvironmentDiscovery)
async def discover_university_environment(request: Request) -> EnvironmentDiscovery:
    """Start the adaptive onboarding process for a university.

    A production connector supplies authoritative page/system metadata. The platform
    should not replace an existing university service unless the university opts in.
    """
    tenant_id = getattr(request.state, "tenant_id", "default")
    return EnvironmentDiscovery(
        tenant_id=tenant_id,
        discovered_pages=[],
        discovered_features=[],
        recommended_actions=[
            "Connect the university source registry",
            "Map existing pages and services",
            "Select platform modules to activate",
        ],
    )


@router.put("/{feature_key}", response_model=FeatureDescriptor)
async def configure_feature(request: Request, feature_key: str, payload: FeatureActivation) -> FeatureDescriptor:
    if feature_key not in SUPPORTED_FEATURES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Unknown platform feature")
    return FeatureDescriptor(
        feature_key=feature_key,
        enabled=payload.enabled,
        integration_mode=payload.integration_mode,
        external_endpoint=payload.external_endpoint,
    )
