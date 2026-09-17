from fastapi import APIRouter, Request, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

router = APIRouter()

class DisciplineAttachment(BaseModel):
    type: str  # code_repo, cad_drawing, hi_res_image, video, research_paper_pdf, slides
    url: str
    title: str

class ProjectSubmitRequest(BaseModel):
    title: str
    discipline: str  # computer_science, engineering, arts_design, business, medicine, humanities
    abstract: str
    department_id: str
    supervisor_id: str
    attachments: List[DisciplineAttachment] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

class ProjectReviewAction(BaseModel):
    action: str  # approve, reject, request_changes
    comments: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    title: str
    slug: str
    discipline: str
    department: str
    supervisor_id: Optional[str]
    status: str  # draft, submitted, under_review, approved, published, rejected
    attachments: List[DisciplineAttachment]
    tags: List[str]
    public_url: str

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    request: Request,
    department: Optional[str] = None,
    discipline: Optional[str] = None,
    status_filter: Optional[str] = "published"
):
    tenant_id = getattr(request.state, "tenant_id", "default")
    return [
        ProjectResponse(
            id="prj_881",
            title="Smart Multi-Tenant Cloud Core",
            slug="smart-multi-tenant-cloud-core",
            discipline=discipline or "computer_science",
            department=department or "Software Engineering",
            supervisor_id="usr_prof_1",
            status=status_filter or "published",
            attachments=[
                DisciplineAttachment(type="code_repo", url="https://github.com/mhommdkuyr/University", title="GitHub Repository"),
                DisciplineAttachment(type="research_paper_pdf", url="https://storage.platform.edu/papers/881.pdf", title="Architecture Specification")
            ],
            tags=["cloud", "saas", "fastapi"],
            public_url=f"https://{tenant_id}.platform.edu/projects/smart-multi-tenant-cloud-core"
        )
    ]

@router.post("/submit", response_model=ProjectResponse)
async def submit_project(request: Request, payload: ProjectSubmitRequest):
    tenant_id = getattr(request.state, "tenant_id", "default")
    slug = payload.title.lower().replace(" ", "-")
    return ProjectResponse(
        id="prj_new_101",
        title=payload.title,
        slug=slug,
        discipline=payload.discipline,
        department="Requested Department",
        supervisor_id=payload.supervisor_id,
        status="under_review",
        attachments=payload.attachments,
        tags=payload.tags,
        public_url=f"https://{tenant_id}.platform.edu/projects/{slug}"
    )

@router.post("/{project_id}/review", response_model=ProjectResponse)
async def review_project(project_id: str, payload: ProjectReviewAction, request: Request):
    tenant_id = getattr(request.state, "tenant_id", "default")
    new_status = "published" if payload.action == "approve" else ("rejected" if payload.action == "reject" else "under_review")
    return ProjectResponse(
        id=project_id,
        title="Smart Multi-Tenant Cloud Core",
        slug="smart-multi-tenant-cloud-core",
        discipline="computer_science",
        department="Software Engineering",
        supervisor_id="usr_prof_1",
        status=new_status,
        attachments=[],
        tags=["cloud"],
        public_url=f"https://{tenant_id}.platform.edu/projects/smart-multi-tenant-cloud-core"
    )
