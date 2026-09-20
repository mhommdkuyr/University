from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Project, get_session


router = APIRouter()


class SearchResultItem(BaseModel):
    type: str
    title: str
    score: float
    url: str


@router.get("/semantic", response_model=list[SearchResultItem])
async def semantic_search(
    request: Request,
    q: str,
    session: AsyncSession = Depends(get_session),
):
    tenant_id = request.headers.get("X-Tenant-ID") or getattr(request.state, "tenant_id", "default")
    query = select(Project).where(Project.tenant_id == tenant_id, Project.status == "approved")
    rows = (await session.scalars(query)).all()

    needle = q.strip().lower()
    results = []
    for row in rows:
        haystack = f"{row.title} {row.description} {row.department}".lower()
        if needle in haystack:
            score = 1.0
        else:
            score = 0.25
        results.append(
            SearchResultItem(
                type="project",
                title=row.title,
                score=score,
                url=row.public_url,
            )
        )

    return sorted(results, key=lambda item: item.score, reverse=True)[:50]
