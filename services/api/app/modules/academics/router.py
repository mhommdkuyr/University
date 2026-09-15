from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class CourseSchema(BaseModel):
    code: str
    title: str
    credits: int

@router.get("/courses", response_model=List[CourseSchema])
async def list_courses():
    return [
        {"code": "SWE-432", "title": "Cloud Architecture", "credits": 3},
        {"code": "CS-301", "title": "Distributed Databases", "credits": 3}
    ]
