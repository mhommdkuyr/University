"""Tenant feature and UI policy primitives."""
from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class IntegrationMode(str, Enum):
    PLATFORM = "platform"
    EXTERNAL = "external"
    HIDDEN = "hidden"


@dataclass(frozen=True)
class FeaturePolicy:
    key: str
    enabled: bool
    integration_mode: IntegrationMode = IntegrationMode.PLATFORM
    external_endpoint: str | None = None


DEFAULT_FEATURES: Mapping[str, str] = {
    "attendance": "الحضور والغياب",
    "schedule": "الجداول",
    "lectures": "المحاضرات والمواد التعليمية",
    "news": "الأخبار والإعلانات",
    "public_projects": "المشاريع العامة",
    "ai_assistant": "مساعد الذكاء الاصطناعي",
    "requests": "الخدمات والطلبات",
    "campus_map": "خريطة الحرم",
}


def resolve_feature(
    key: str,
    *,
    enabled: bool,
    integration_mode: IntegrationMode,
    external_endpoint: str | None = None,
) -> FeaturePolicy:
    if key not in DEFAULT_FEATURES:
        raise ValueError(f"Unknown feature: {key}")
    if integration_mode == IntegrationMode.EXTERNAL and not external_endpoint:
        raise ValueError("external_endpoint is required for external integration")
    return FeaturePolicy(
        key=key,
        enabled=enabled,
        integration_mode=integration_mode,
        external_endpoint=external_endpoint,
    )
