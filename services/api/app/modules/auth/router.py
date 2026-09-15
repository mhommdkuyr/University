from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    return {
        "access_token": "mock_jwt_token_sample",
        "token_type": "bearer",
        "tenant_id": "tenant_sample"
    }
