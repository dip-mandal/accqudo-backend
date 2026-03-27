# backend/app/services/tenant/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import json

from app.db.session import get_db
from app.db.models import Tenant
from app.core.redis import redis_client  # Import our Redis pool

from app.api.dependencies import get_current_user
from app.db.models import TenantModule, Module, Publication
from sqlalchemy import func
from app.db.models import Publication, Project # Ensure Project is imported!

router = APIRouter()

# backend/app/services/tenant/router.py
# (Find and replace this specific endpoint at the bottom)



@router.get("/public/{subdomain}")
async def get_public_tenant_data(subdomain: str, db: AsyncSession = Depends(get_db)):
    """
    Public endpoint. No JWT required. 
    Fetches all public data for the edge-rendered portfolio website.
    """
    # 1. Fetch Tenant
    result = await db.execute(select(Tenant).where(Tenant.subdomain == subdomain))
    tenant = result.scalars().first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Website not found")

    # 2. Fetch Active Modules (To know what UI sections to render)
    modules_result = await db.execute(
        select(Module.key)
        .join(TenantModule)
        .where(TenantModule.tenant_id == tenant.id, TenantModule.is_active == True)
    )
    active_modules = modules_result.scalars().all()

    # 3. Fetch Core Data (Publications)
    pub_result = await db.execute(
        select(Publication).where(Publication.tenant_id == tenant.id).order_by(Publication.year.desc())
    )
    publications = pub_result.scalars().all()

    # 4. Fetch Premium Data (Projects - Only if they own the module!)
    projects = []
    if "projects" in active_modules:
        proj_result = await db.execute(
            select(Project).where(Project.tenant_id == tenant.id).order_by(Project.start_year.desc())
        )
        projects = proj_result.scalars().all()

    return {
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "subdomain": tenant.subdomain
        },
        "active_modules": active_modules,
        "publications": publications,
        "projects": projects
    }



# backend/app/services/tenant/router.py (Add to bottom)

@router.get("/me/dashboard-stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = current_user["tenant_id"]

    # 1. Get real active modules for this specific tenant
    modules_query = select(Module).join(TenantModule).where(
        TenantModule.tenant_id == tenant_id,
        TenantModule.is_active == True
    )
    modules_result = await db.execute(modules_query)
    active_modules = [m.key for m in modules_result.scalars().all()]

    # 2. Get real publication count
    pub_query = select(func.count(Publication.id)).where(Publication.tenant_id == tenant_id)
    pub_result = await db.execute(pub_query)
    pub_count = pub_result.scalar()

    return {
        "tenant_id": tenant_id,
        "active_modules": active_modules,
        "publication_count": pub_count
    }