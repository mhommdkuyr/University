from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class ProjectResponse(BaseModel):
    id: str
    title: str
    slug: str
    department: str
    status: str
    public_url: str

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    request: Request,
    department: Optional[str] = None,
    tag: Optional[str] = None
):
    tenant_id = getattr(request.state, "tenant_id", "default")
    return [
        {
            "id": "prj_881",
            "title": "Smart Multi-Tenant Cloud Core",
            "slug": "smart-multi-tenant-cloud-core",
            "department": department or "Software Engineering",
            "status": "approved",
            "public_url": f"https://{tenant_id}.platform.edu/projects/smart-multi-tenant-cloud-core"
        }
    ]
