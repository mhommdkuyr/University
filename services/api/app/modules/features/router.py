from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import Permission, request_access_context
from app.core.database import FeatureRecord, get_session
from app.core.feature_policy import DEFAULT_FEATURES, IntegrationMode, resolve_feature


router = APIRouter()


class FeatureDescriptor(BaseModel):
    feature_key: str
    enabled: bool
    integration_mode: str
    existing_page_detected: bool = False
    external_endpoint: str | None = None


class EnvironmentDiscovery(BaseModel):
    tenant_id: str
    discovered_pages: list[str]
    discovered_features: list[str]
    recommended_actions: list[str]


class FeatureActivation(BaseModel):
    feature_key: str
    enabled: bool
    integration_mode: IntegrationMode = IntegrationMode.PLATFORM
    external_endpoint: str | None = None


@router.get("/catalog", response_model=list[FeatureDescriptor])
async def feature_catalog(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        return [
            FeatureDescriptor(feature_key=key, enabled=False, integration_mode=IntegrationMode.PLATFORM.value)
            for key in DEFAULT_FEATURES
        ]

    result = []
    for key in DEFAULT_FEATURES:
        record = await session.scalar(
            select(FeatureRecord).where(
                FeatureRecord.tenant_id == tenant_id,
                FeatureRecord.feature_key == key,
            )
        )
        result.append(
            FeatureDescriptor(
                feature_key=key,
                enabled=record.enabled if record else False,
                integration_mode=record.integration_mode if record else IntegrationMode.PLATFORM.value,
                external_endpoint=record.external_endpoint if record else None,
            )
        )
    return result


@router.post("/discover", response_model=EnvironmentDiscovery)
async def discover_university_environment(request: Request):
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
async def configure_feature(
    request: Request,
    feature_key: str,
    payload: FeatureActivation,
    session: AsyncSession = Depends(get_session),
):
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

    record = await session.scalar(
        select(FeatureRecord).where(
            FeatureRecord.tenant_id == context.tenant_id,
            FeatureRecord.feature_key == feature_key,
        )
    )
    if record is None:
        session.add(FeatureRecord(
            id=str(uuid4()),
            tenant_id=context.tenant_id,
            feature_key=feature_key,
            enabled=policy.enabled,
            integration_mode=policy.integration_mode.value,
            external_endpoint=policy.external_endpoint,
        ))
    else:
        record.enabled = policy.enabled
        record.integration_mode = policy.integration_mode.value
        record.external_endpoint = policy.external_endpoint

    await session.commit()
    return FeatureDescriptor(
        feature_key=policy.key,
        enabled=policy.enabled,
        integration_mode=policy.integration_mode.value,
        external_endpoint=policy.external_endpoint,
    )
