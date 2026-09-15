from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import List

router = APIRouter()

class SearchResultItem(BaseModel):
    type: str
    title: str
    score: float
    url: str

@router.get("/semantic", response_model=List[SearchResultItem])
async def semantic_search(request: Request, q: str = Query(..., description="Natural language search query")):
    tenant_id = getattr(request.state, "tenant_id", "default")
    return [
        {
            "type": "project",
            "title": "Smart Multi-Tenant Cloud Core",
            "score": 0.94,
            "url": f"https://{tenant_id}.platform.edu/projects/smart-multi-tenant-cloud-core"
        }
    ]
