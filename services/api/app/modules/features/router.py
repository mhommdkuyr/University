from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.access_control import Permission, request_access_context
from app.core.feature_policy import DEFAULT_FEATURES, IntegrationMode, resolve_feature

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
    integration_mode: IntegrationMode = IntegrationMode.PLATFORM
    external_endpoint: Optional[str] = None


@router.get("/catalog", response_model=List[FeatureDescriptor])
async def feature_catalog() -> List[FeatureDescriptor]:
    return [
        FeatureDescriptor(feature_key=key, enabled=False, integration_mode=IntegrationMode.PLATFORM.value)
        for key in DEFAULT_FEATURES
    ]


@router.post("/discover", response_model=EnvironmentDiscovery)
async def discover_university_environment(request: Request) -> EnvironmentDiscovery:
    """Start the adaptive onboarding process for a university."""
    context = request_access_context(request)
    if Permission.MANAGE_UNIVERSITY not in context.permissions:
        raise HTTPException(status_code=403, detail="University environment discovery denied")
    return EnvironmentDiscovery(
        tenant_id=context.tenant_id,
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
    context = request_access_context(request)
    if Permission.MANAGE_UNIVERSITY not in context.permissions:
        raise HTTPException(status_code=403, detail="Feature configuration denied")
    try:
        policy = resolve_feature(
            feature_key,
            enabled=payload.enabled,
            integration_mode=payload.integration_mode,
            external_endpoint=payload.external_endpoint,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FeatureDescriptor(
        feature_key=policy.key,
        enabled=policy.enabled,
        integration_mode=policy.integration_mode.value,
        external_endpoint=policy.external_endpoint,
    )
