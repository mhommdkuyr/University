from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter()

class FacultySchema(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

class DepartmentSchema(BaseModel):
    id: str
    faculty_id: str
    name: str
    code: str

class ProgramSchema(BaseModel):
    id: str
    department_id: str
    name: str
    degree_type: str

class CourseSchema(BaseModel):
    id: str
    department_id: str
    code: str
    title: str
    credits: int

class EnrollmentSchema(BaseModel):
    id: str
    student_id: str
    course_id: str
    semester: str
    status: str

@router.get("/faculties", response_model=List[FacultySchema])
async def list_faculties(request: Request):
    tenant_id = getattr(request.state, "tenant_id", "default")
    return [
        FacultySchema(id="fac_1", name="Faculty of Engineering & Computer Science", description="Engineering & Computing"),
        FacultySchema(id="fac_2", name="Faculty of Business Administration", description="Business & Finance")
    ]

@router.get("/departments", response_model=List[DepartmentSchema])
async def list_departments(request: Request, faculty_id: Optional[str] = None):
    return [
        DepartmentSchema(id="dept_1", faculty_id="fac_1", name="Software Engineering", code="SWE"),
        DepartmentSchema(id="dept_2", faculty_id="fac_1", name="Computer Science", code="CS")
    ]

@router.get("/courses", response_model=List[CourseSchema])
async def list_courses(request: Request, department_id: Optional[str] = None):
    return [
        CourseSchema(id="crs_1", department_id="dept_1", code="SWE-432", title="Cloud Architecture", credits=3),
        CourseSchema(id="crs_2", department_id="dept_2", code="CS-301", title="Distributed Databases", credits=3)
    ]

@router.get("/enrollments", response_model=List[EnrollmentSchema])
async def list_student_enrollments(request: Request, student_id: Optional[str] = None):
    return [
        EnrollmentSchema(id="enr_1", student_id=student_id or "std_101", course_id="crs_1", semester="Fall 2026", status="registered")
    ]
