from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class TenantItem(BaseModel):
    slug: str
    name: str
    plan: str
    status: str

@router.get("/", response_model=List[TenantItem])
async def list_tenants():
    return [
        {"slug": "ksu", "name": "King Saud University", "plan": "enterprise", "status": "active"},
        {"slug": "cu", "name": "Cairo University", "plan": "pro", "status": "active"}
    ]
