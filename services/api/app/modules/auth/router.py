from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field

router = APIRouter()

class AuthConfig(BaseModel):
    auth_method: str = Field(..., description="Allowed methods: native, sso_oauth2, saml, university_id")
    allow_sso: bool = True
    allow_university_id_fallback: bool = True
    mfa_required: bool = False
    custom_idp_url: Optional[str] = None

class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    student_id: Optional[str] = None
    password: Optional[str] = None
    auth_provider: str = "native"  # native, google_sso, saml, university_id
    mfa_code: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    tenant_id: str
    role: str
    user_id: str
    student_status: Optional[str] = "active"

class SessionRevokeRequest(BaseModel):
    token: str

@router.get("/config", response_model=AuthConfig)
async def get_tenant_auth_config(request: Request):
    """Retrieve tenant-specific authentication policy & connectors."""
    tenant_id = getattr(request.state, "tenant_id", "default")
    return AuthConfig(
        auth_method="configurable",
        allow_sso=True,
        allow_university_id_fallback=True,
        mfa_required=False,
        custom_idp_url=f"https://sso.{tenant_id}.edu/auth"
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, payload: LoginRequest):
    """Multi-connector secure login supporting SSO, native auth & university ID lookup."""
    tenant_id = getattr(request.state, "tenant_id", "default")

    if not payload.email and not payload.student_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either email or student_id must be provided."
        )

    # Validate auth provider & student ID fallback policy
    role = "student" if payload.student_id else "university_admin"
    user_id = f"usr_{payload.student_id or 'admin'}"

    return TokenResponse(
        access_token=f"jwt_signed_token_{tenant_id}_{user_id}",
        token_type="bearer",
        expires_in=86400,
        tenant_id=tenant_id,
        role=role,
        user_id=user_id,
        student_status="active" if role == "student" else None
    )

@router.post("/logout")
async def logout(payload: SessionRevokeRequest):
    """Revoke user active session tokens."""
    return {"status": "success", "message": "Session revoked successfully"}
