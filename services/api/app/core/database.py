from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import Request

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings
from app.core.security import hash_password


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    plan: Mapped[str] = mapped_column(String(50), default="starter")
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        UniqueConstraint("tenant_id", "student_number", name="uq_users_tenant_student_number"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(50), default="student", index=True)
    student_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    student_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("tenant_id", "slug", name="uq_projects_tenant_slug"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(160))
    department: Mapped[str] = mapped_column(String(160), default="")
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    public_url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_courses_tenant_code"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    code: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    credits: Mapped[int] = mapped_column(Integer, default=3)
    content: Mapped[str] = mapped_column(Text, default="")
    published: Mapped[bool] = mapped_column(Boolean, default=True)


class StudentGroup(Base):
    __tablename__ = "student_groups"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    course_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    student_ids: Mapped[str] = mapped_column(Text, default="[]")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    student_id: Mapped[str] = mapped_column(String(64), index=True)
    course_id: Mapped[str] = mapped_column(String(64), index=True)
    present: Mapped[bool] = mapped_column(Boolean, default=False)
    recorded_by: Mapped[str] = mapped_column(String(64))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RolePolicyRecord(Base):
    __tablename__ = "role_policies"
    __table_args__ = (UniqueConstraint("tenant_id", "role", name="uq_role_policies_tenant_role"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    role: Mapped[str] = mapped_column(String(50))
    permissions: Mapped[str] = mapped_column(Text, default="[]")


class FeatureRecord(Base):
    __tablename__ = "feature_policies"
    __table_args__ = (UniqueConstraint("tenant_id", "feature_key", name="uq_features_tenant_key"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    feature_key: Mapped[str] = mapped_column(String(100))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    integration_mode: Mapped[str] = mapped_column(String(30), default="platform")
    external_endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    resource_type: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40))
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


connect_args = {}
if settings.DATABASE_URL.startswith("postgresql") and settings.DATABASE_SSL_MODE:
    connect_args["ssl"] = settings.DATABASE_SSL_MODE

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        await set_tenant_context(session, getattr(request.state, "tenant_id", None))
        yield session


async def set_tenant_context(session: AsyncSession, tenant_id: str | None) -> None:
    if not tenant_id or tenant_id == "default":
        return
    if session.get_bind().dialect.name != "postgresql":
        return
    await session.execute(
        text("SET LOCAL app.tenant_id = :tenant_id"),
        {"tenant_id": tenant_id},
    )
async def init_db() -> None:
    if not settings.AUTO_CREATE_SCHEMA and settings.ENVIRONMENT == "production":
        return

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    if not settings.SEED_DEMO_DATA:
        return

    async with SessionLocal() as session:
        tenant = await session.scalar(select(Tenant).where(Tenant.id == "demo"))
        if tenant is None:
            session.add(Tenant(id="demo", name="Demo University", slug="demo", plan="pilot", status="active"))

        student = await session.scalar(select(User).where(User.tenant_id == "demo", User.email == "student@demo.edu"))
        if student is None:
            session.add(User(
                id="demo-student", tenant_id="demo", email="student@demo.edu",
                password_hash=hash_password("DemoStudent123!"), role="student",
                student_status="active", student_number="DEMO-1001",
                full_name="Demo Active Student",
            ))

        president = await session.scalar(select(User).where(User.tenant_id == "demo", User.email == "president@demo.edu"))
        if president is None:
            session.add(User(
                id="demo-president", tenant_id="demo", email="president@demo.edu",
                password_hash=hash_password("DemoPresident123!"), role="university_president",
                full_name="Demo University President",
            ))

        admin = await session.scalar(select(User).where(User.tenant_id == "demo", User.email == "admin@platform.local"))
        if admin is None:
            session.add(User(
                id="platform-admin", tenant_id="demo", email="admin@platform.local",
                password_hash=hash_password("DemoAdmin12345!"), role="platform_admin",
                full_name="Platform Administrator",
            ))

        project = await session.scalar(
            select(Project).where(Project.tenant_id == "demo", Project.slug == "smart-multi-tenant-cloud-core")
        )
        if project is None:
            session.add(Project(
                id="prj-demo", tenant_id="demo", owner_id="demo-student",
                title="Smart Multi-Tenant Cloud Core",
                slug="smart-multi-tenant-cloud-core",
                department="Software Engineering", status="approved",
                description="Demo project used only for local/pilot validation.",
                public_url="https://demo.platform.edu/projects/smart-multi-tenant-cloud-core",
            ))

        course = await session.scalar(select(Course).where(Course.tenant_id == "demo", Course.code == "SWE-432"))
        if course is None:
            session.add_all([
                Course(id="course-swe-432", tenant_id="demo", code="SWE-432", title="Cloud Architecture", credits=3, published=True),
                Course(id="course-cs-301", tenant_id="demo", code="CS-301", title="Distributed Databases", credits=3, published=True),
            ])

        await session.commit()
